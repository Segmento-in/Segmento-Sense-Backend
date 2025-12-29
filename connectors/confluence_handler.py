import pandas as pd
from atlassian import Confluence
from bs4 import BeautifulSoup

class ConfluenceHandler:
    def __init__(self):
        print("✅ Confluence Handler loaded.")

    def fetch_page_content(self, url, username, api_token, page_id):
        """
        Fetches the body content of a specific Confluence page.
        """
        try:
            # Initialize Confluence API
            confluence = Confluence(
                url=url,
                username=username,
                password=api_token,
                cloud=True
            )

            # Get Page Content
            page = confluence.get_page_by_id(page_id, expand='body.storage')
            title = page.get('title', 'Unknown Title')
            
            # Extract HTML body
            raw_html = page.get('body', {}).get('storage', {}).get('value', '')

            # Clean HTML tags to get raw text for PII scanning
            if raw_html:
                clean_text = BeautifulSoup(raw_html, "html.parser").get_text(separator=' ')
            else:
                clean_text = ""

            return pd.DataFrame([{
                "Source": "Confluence",
                "Sender": username,
                "Subject": title,
                "Content": clean_text
            }])

        except Exception as e:
            print(f"❌ Confluence Error: {e}")
            return pd.DataFrame()