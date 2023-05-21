import logging
import os

from telegram import Update
from telegram.ext import Application, ContextTypes, MessageHandler, filters
from yt_dlp import YoutubeDL

FOLDER_PATH = os.getenv("FOLDER_PATH")
TG_TOKEN = os.getenv("TG_BOT_TOKEN")

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)


def download_yt(yt_link: str):
    params = {
        "format": "bestaudio/best",
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
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


async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Echo the user message."""
    url = update.message.text
    if not url.startswith("https://youtu.be/"):
        await update.message.reply_text("It is not youtube link")
        return
    download_yt(url)
    new_files = get_new_files()
    for filename in new_files:
        file_path = f"{FOLDER_PATH}/{filename}"
        await update.message.chat.send_audio(file_path)
        os.remove(file_path)


def main() -> None:
    application = Application.builder().token(TG_TOKEN).build()

    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

    application.run_polling()


if __name__ == "__main__":
    main()
