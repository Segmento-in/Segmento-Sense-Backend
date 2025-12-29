import base64
import os
import pickle
import pandas as pd
from bs4 import BeautifulSoup
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

class GmailHandler:
    def __init__(self):
        print("✅ Gmail Handler loaded.")

    def fetch_emails(self, credentials_file, num_emails=10) -> pd.DataFrame:
        """
        Authenticates and fetches emails from Gmail.
        """
        try:
            SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
            creds = None
            token_path = 'token.pickle'
            
            if os.path.exists(token_path):
                with open(token_path, 'rb') as token:
                    creds = pickle.load(token)
            
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    # Write temp file because flow requires file path
                    with open("temp_client_secret.json", "wb") as f:
                        f.write(credentials_file.getvalue())
                    
                    flow = InstalledAppFlow.from_client_secrets_file('temp_client_secret.json', SCOPES)
                    creds = flow.run_local_server(port=0)
                    
                    with open(token_path, 'wb') as token:
                        pickle.dump(creds, token)
                    
                    if os.path.exists("temp_client_secret.json"):
                        os.remove("temp_client_secret.json")

            service = build('gmail', 'v1', credentials=creds)
            results = service.users().messages().list(userId='me', maxResults=num_emails).execute()
            messages = results.get('messages', [])
            
            email_data = []
            for message in messages:
                msg = service.users().messages().get(userId='me', id=message['id']).execute()
                payload = msg['payload']
                headers = payload.get("headers")
                
                subject = next((h['value'] for h in headers if h['name'] == 'Subject'), "No Subject")
                sender = next((h['value'] for h in headers if h['name'] == 'From'), "Unknown")

                body = ""
                if 'parts' in payload:
                    for part in payload['parts']:
                        if part['mimeType'] == 'text/plain' and 'data' in part['body']:
                            body += base64.urlsafe_b64decode(part['body']['data']).decode()
                elif 'body' in payload and 'data' in payload['body']:
                     body += base64.urlsafe_b64decode(payload['body']['data']).decode()

                clean_body = BeautifulSoup(body, "html.parser").get_text()
                email_data.append({
                    "Source": "Gmail",
                    "Sender": sender,
                    "Subject": subject,
                    "Content": f"Subject: {subject}\n\n{clean_body}"
                })
            
            return pd.DataFrame(email_data)

        except Exception as e:
            print(f"❌ Gmail Error: {e}")
            return pd.DataFrame()