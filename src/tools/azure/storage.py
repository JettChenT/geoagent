from azure.identity import DefaultAzureCredential
import os
import uuid
import dotenv
from azure.storage.blob import BlobServiceClient

dotenv.load_dotenv()

STORAGE_ACC = os.getenv("AZ_STORAGE_ACCOUNT_NAME")
account_url = f"https://{STORAGE_ACC}.blob.core.windows.net"
defauth = DefaultAzureCredential()
blob_service_client = BlobServiceClient(account_url, credential=defauth)

container_name = os.getenv("AZ_STORAGE_CONTAINER_NAME") or "geolocationcnt"
container_client = blob_service_client.get_container_client(container_name)

# Create a local directory to hold blob data
local_path = "./data"
if not os.path.exists(local_path):
    os.mkdir(local_path)

# Create a file in the local data directory to upload and download
local_file_name = str(uuid.uuid4()) + ".txt"
upload_file_path = os.path.join(local_path, local_file_name)

# Write text to the file
file = open(file=upload_file_path, mode="w")
file.write("Hello, World!")
file.close()

# Create a blob client using the local file name as the name for the blob
blob_client = blob_service_client.get_blob_client(
    container=container_name, blob=local_file_name
)

print("\nUploading to Azure Storage as blob:\n\t" + local_file_name)

# Upload the created file
# with open(file=upload_file_path, mode="rb") as data:
#     blob_client.upload_blob(data)

blob_list = container_client.list_blobs()
for l in blob_list:
    print(l)
