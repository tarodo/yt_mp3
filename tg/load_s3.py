from datetime import timedelta
from pathlib import Path

from minio import Minio
from minio.error import S3Error
import logging
from urllib.parse import urlsplit, urlunsplit

logger = logging.getLogger(__name__)


def upload_file_to_minio(file_path: Path, bucket_name):
    file_name = file_path.name
    logger.info(f"Start send file :: {file_name}")
    client = Minio(
        "localhost:9000",
        access_key="myminioadmin",
        secret_key="minipass",
        secure=False
    )

    # Создаем корзину, если она еще не существует
    if not client.bucket_exists(bucket_name):
        client.make_bucket(bucket_name)

    # Загружаем файл
    client.fput_object(bucket_name, file_name, file_path)

    # Генерируем пресекретный URL для скачивания файла
    # URL будет действовать 24 часа (1440 минут)
    presigned_url = client.presigned_get_object(bucket_name, file_name, expires=timedelta(minutes=1440))
    # scheme, netloc, path, query, fragment = urlsplit(presigned_url)
    # netloc = 'localhost:9000'
    # url = urlunsplit((scheme, netloc, path, query, fragment))
    # logger.info(f"NEW URL :: {url}")
    return presigned_url


# url = upload_file_to_minio("./load_s3.py", "torw")
#
# import requests
# response = requests.get(url)
# response.raise_for_status()
# with open('my_downloaded_file', 'wb') as f:
#     f.write(response.content)
