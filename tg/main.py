import logging
import os
import re
from pathlib import Path

from load_s3 import get_minio_client, upload_file_to_minio
from telegram import Update
from telegram.ext import Application, ContextTypes, MessageHandler, filters
from yt_dlp import YoutubeDL

FOLDER_PATH = os.getenv("FOLDER_PATH")
TG_TOKEN = os.getenv("TG_BOT_TOKEN")
FILE_LENGTH = int(os.getenv("FILE_LENGTH_MIN", 15))
BUCKET_NAME = os.getenv("BUCKET_NAME")

MINIO_HOST = os.getenv("MINIO_HOST")
MINIO_PORT = os.getenv("MINIO_PORT")
MINIO_USER = os.getenv("MINIO_USER")
MINIO_PASS = os.getenv("MINIO_PASS")

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
        "outtmpl": f"{FOLDER_PATH}/%(title).100s",
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
    for filename in sorted(os.listdir(FOLDER_PATH), reverse=True):
        file_path = os.path.join(FOLDER_PATH, filename)
        if os.path.isfile(file_path):
            result.append(filename)
    return result


def clear_file_name(file_name: str) -> str:
    file_name = file_name.strip()
    file_name = re.sub(r"[^\w\s]+", "", file_name)
    file_name = " ".join(file_name.split())
    return file_name


async def send_s3_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.chat_id
    for filename in get_new_files():
        file_path = Path(f"{FOLDER_PATH}/{filename}")
        if file_path.suffix == ".mp3":
            client = get_minio_client(MINIO_HOST, MINIO_PORT, MINIO_USER, MINIO_PASS)
            new_url = upload_file_to_minio(client, file_path, str(user_id))
            await update.message.chat.send_message(
                text=f"[{clear_file_name(file_path.stem)}]({new_url})",
                parse_mode="Markdown",
            )


async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    url = update.message.text
    if not url.startswith(YOUTUBE_BASE_LINKS):
        await update.message.reply_text("It is not youtube link")
        return
    download_yt(url)
    try:
        await send_s3_link(update, context)
    except Exception as e:
        logger.error(f"An error occurred :: {e}")
    finally:
        for filename in get_new_files():
            file_path = Path(f"{FOLDER_PATH}/{filename}")
            os.remove(file_path)


def main() -> None:
    application = Application.builder().token(TG_TOKEN).build()

    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

    application.run_polling()


if __name__ == "__main__":
    main()
