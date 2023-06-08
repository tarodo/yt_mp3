import logging
from datetime import timedelta
from pathlib import Path

from minio import Minio

logger = logging.getLogger(__name__)


def get_minio_client(url: str, port: str, user: str, secret: str) -> Minio:
    return Minio(f"{url}:{port}", access_key=user, secret_key=secret, secure=False)


def upload_file_to_minio(client: Minio, file_path: Path, bucket_name: str):
    file_name = file_path.name
    logger.info(f"Start send file :: {file_name}")

    if not client.bucket_exists(bucket_name):
        client.make_bucket(bucket_name)
    try:
        client.fput_object(bucket_name, file_name, file_path)

        presigned_url = client.presigned_get_object(
            bucket_name, file_name, expires=timedelta(minutes=1440)
        )
        logger.info(f"File sent successfully, presigned url :: {presigned_url}")
        return presigned_url
    except Exception as err:
        logger.error(f"An error occurred while uploading file to Minio :: {err}")
