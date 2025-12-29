import io
import json
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from google.oauth2 import service_account

class DriveHandler:
    def __init__(self):
        print("✅ Google Drive Handler loaded.")

    def list_files(self, credentials_dict):
        try:
            creds = service_account.Credentials.from_service_account_info(
                credentials_dict, scopes=['https://www.googleapis.com/auth/drive.readonly']
            )
            service = build('drive', 'v3', credentials=creds)
            results = service.files().list(
                pageSize=15, fields="files(id, name, mimeType)"
            ).execute()
            return results.get('files', [])
        except Exception as e:
            print(f"❌ Drive List Error: {e}")
            return []

    def download_file(self, file_id, mime_type, credentials_dict) -> bytes:
        try:
            creds = service_account.Credentials.from_service_account_info(
                credentials_dict, scopes=['https://www.googleapis.com/auth/drive.readonly']
            )
            service = build('drive', 'v3', credentials=creds)
            
            # Export Google Docs to standard formats
            if "spreadsheet" in mime_type:
                request = service.files().export_media(fileId=file_id, mimeType='text/csv')
            elif "document" in mime_type:
                request = service.files().export_media(fileId=file_id, mimeType='application/pdf')
            elif "presentation" in mime_type:
                request = service.files().export_media(fileId=file_id, mimeType='application/pdf')
            else:
                # Download binary files directly
                request = service.files().get_media(fileId=file_id)
            
            fh = io.BytesIO()
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while done is False:
                status, done = downloader.next_chunk()
            
            return fh.getvalue()
        except Exception as e:
            print(f"❌ Drive Download Error: {e}")
            return b""