from azure.storage.blob import BlobServiceClient

class AzureBlobHandler:
    def __init__(self):
        print("✅ Azure Blob Handler loaded.")

    def get_containers(self, conn_str):
        try:
            blob_service_client = BlobServiceClient.from_connection_string(conn_str)
            containers = blob_service_client.list_containers()
            return [c['name'] for c in containers]
        except Exception as e:
            print(f"❌ Azure Error: {e}")
            return []

    def get_blobs(self, conn_str, container_name):
        try:
            blob_service_client = BlobServiceClient.from_connection_string(conn_str)
            container_client = blob_service_client.get_container_client(container_name)
            blobs = container_client.list_blobs()
            return [b['name'] for b in blobs]
        except Exception as e:
            return []

    def download_blob(self, conn_str, container_name, blob_name):
        try:
            blob_service_client = BlobServiceClient.from_connection_string(conn_str)
            blob_client = blob_service_client.get_blob_client(container=container_name, blob=blob_name)
            return blob_client.download_blob().readall()
        except Exception as e:
            print(f"❌ Azure Download Error: {e}")
            return b""