from google.cloud import storage
from pathlib import Path
import os


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
    bucket_name = bucket_name or os.getenv("GCP_BUCKET_NAME") or "geolocation"
    destination_blob_name = destination_blob_name or file_path.name
    storage_client = storage.Client()
    bucket = storage_client.create_bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)
    blob.upload_from_filename(file_path)
    blob.make_public()
    return blob.public_url


#!/usr/bin/env python

# Copyright 2016 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


def run_quickstart():
    # [START storage_quickstart]
    # Imports the Google Cloud client library
    from google.cloud import storage

    # Instantiates a client
    storage_client = storage.Client()

    # The name for the new bucket
    bucket_name = "my-new-bucket"

    # Creates the new bucket
    bucket = storage_client.create_bucket(bucket_name)

    print(f"Bucket {bucket.name} created.")
    # [END storage_quickstart]


if __name__ == "__main__":
    # from dotenv import load_dotenv
    # load_dotenv()
    # upload_file(Path('./images/anon/10.png'))
    run_quickstart()
