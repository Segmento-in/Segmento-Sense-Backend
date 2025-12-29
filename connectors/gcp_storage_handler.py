from google.cloud import storage
from google.oauth2 import service_account

class GcpStorageHandler:
    def __init__(self):
        print("✅ GCP Storage Handler loaded.")

    def get_buckets(self, credentials_dict):
        try:
            credentials = service_account.Credentials.from_service_account_info(credentials_dict)
            storage_client = storage.Client(credentials=credentials, project=credentials_dict.get('project_id'))
            buckets = storage_client.list_buckets()
            return [bucket.name for bucket in buckets]
        except Exception as e:
            print(f"❌ GCP Bucket Error: {e}")
            return []

    def get_files(self, credentials_dict, bucket_name):
        try:
            credentials = service_account.Credentials.from_service_account_info(credentials_dict)
            storage_client = storage.Client(credentials=credentials, project=credentials_dict.get('project_id'))
            blobs = storage_client.list_blobs(bucket_name)
            return [blob.name for blob in blobs]
        except Exception as e:
            print(f"❌ GCP List Error: {e}")
            return []

    def download_file(self, credentials_dict, bucket_name, blob_name):
        try:
            credentials = service_account.Credentials.from_service_account_info(credentials_dict)
            storage_client = storage.Client(credentials=credentials, project=credentials_dict.get('project_id'))
            bucket = storage_client.bucket(bucket_name)
            blob = bucket.blob(blob_name)
            return blob.download_as_bytes()
        except Exception as e:
            print(f"❌ GCP Download Error: {e}")
            return b""