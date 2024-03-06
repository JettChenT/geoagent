from google.cloud import storage
from pathlib import Path
import os
import uuid
from functools import cache
import backoff


@cache
@backoff.on_exception(backoff.expo, Exception, max_tries=5)
def upload_file(
    file_path: Path, bucket_name: str = None, destination_blob_name: str = None
):
    """
    Uploads a file to a bucket.
    :param bucket_name: The bucket to upload to.
    :param file_path: The path to the file to upload.
    :param destination_blob_name: The name of the blob to create.
    :return:
    """
    bucket_name = bucket_name or os.getenv("GCP_BUCKET_NAME") or f"geolocation_{uuid.uuid4()}"
    destination_blob_name = destination_blob_name or file_path.name
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)
    blob.upload_from_filename(file_path)
    blob.make_public()
    return blob.public_url


def run_quickstart():
    from google.cloud import storage
    storage_client = storage.Client()
    bucket_name = f"geolocation{uuid.uuid4()}"
    bucket = storage_client.create_bucket(bucket_name)
    print(f"Bucket {bucket.name} created.")

if __name__ == "__main__":
    print(upload_file(Path("./images/gusmeme.png")))
