import logging
import os, psutil

from telegram import Update
from telegram.ext import Application, ContextTypes, MessageHandler, filters
from yt_dlp import YoutubeDL

from pydub import AudioSegment
from pathlib import Path

FOLDER_PATH = os.getenv("FOLDER_PATH")
TG_TOKEN = os.getenv("TG_BOT_TOKEN")
FILE_LENGTH = int(os.getenv("FILE_LENGTH_MIN", 15))

YOUTUBE_BASE_LINKS = ("https://www.youtube.com/", "https://youtu.be/")

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)


def download_yt(yt_link: str):
    logger.info(f"Start file handling :: {yt_link}")
    params = {
        "format": "bestaudio/best",
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "320",
            }
        ],
        "outtmpl": f"{FOLDER_PATH}/%(title).50s",
        "download_archive": None,
        "updatetime": "True",
    }

    with YoutubeDL(params) as ydl:
        ydl.download(
            [
                yt_link,
            ]
        )


def get_new_files():
    result = []
    for filename in os.listdir(FOLDER_PATH):
        file_path = os.path.join(FOLDER_PATH, filename)
        if os.path.isfile(file_path):
            result.append(filename)
    return result


def show_memory(txt: str = "") -> None:
    memory_size = round(psutil.Process(os.getpid()).memory_info().rss / 1024 ** 2, 2)
    logger.info(f"Memory : {memory_size} Mb : {txt}")


def split_mp3_file(file_path: Path) -> int:
    logger.info(f"Start file splitting :: {file_path}")
    audio_size = round(os.path.getsize(file_path) / (1024 ** 2), 2)
    logger.info(f"Audio size :: {audio_size} Mb")
    show_memory("Start split")

    audio = AudioSegment.from_file(file_path)
    show_memory("After AudioSegment loading")

    length = FILE_LENGTH * 60 * 1000
    if len(audio) <= length:
        return 0
    parts = [audio[i:i + length] for i in range(0, len(audio), length)]
    show_memory("Before splitting")
    for i, part in enumerate(parts):
        show_memory(f"{i+1} iteration")
        new_file_name = f"{file_path.stem}_p{i+1}.mp3"
        new_file_path = file_path.with_name(new_file_name)
        part.export(new_file_path, format="mp3")
        segment_size = round(os.path.getsize(new_file_path) / (1024 ** 2), 2)
        logger.info(f"{i+1} segment size :: {segment_size} Mb")
    return len(parts)


def split_files():
    for filename in get_new_files():
        file_path = Path(f"{FOLDER_PATH}/{filename}")
        if not file_path.suffix == ".mp3":
            continue
        parts_cnt = split_mp3_file(file_path)
        if parts_cnt:
            os.remove(file_path)


async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    url = update.message.text
    if not url.startswith(YOUTUBE_BASE_LINKS):
        await update.message.reply_text("It is not youtube link")
        return
    download_yt(url)
    split_files()

    for filename in get_new_files():
        file_path = Path(f"{FOLDER_PATH}/{filename}")
        if file_path.suffix == ".mp3":
            await update.message.chat.send_audio(file_path)
        os.remove(file_path)


def main() -> None:
    application = Application.builder().token(TG_TOKEN).build()

    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

    application.run_polling()


if __name__ == "__main__":
    main()
