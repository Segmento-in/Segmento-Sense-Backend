import pandas as pd
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import datetime

class SlackHandler:
    def __init__(self):
        print("✅ Slack Handler loaded.")

    def fetch_messages(self, token, channel_id, num_messages=20):
        """
        Fetches recent messages from a specific Slack channel.
        """
        try:
            client = WebClient(token=token)
            # Fetch conversation history
            response = client.conversations_history(channel=channel_id, limit=num_messages)
            
            messages = []
            if response['ok']:
                for msg in response['messages']:
                    # Skip subtypes like 'channel_join', only process actual text
                    if 'subtype' not in msg:
                        user_id = msg.get('user', 'Unknown')
                        text = msg.get('text', '')
                        ts = float(msg.get('ts', 0))
                        time_str = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
                        
                        messages.append({
                            "Source": "Slack",
                            "Sender": user_id, 
                            "Subject": f"Message in {channel_id} at {time_str}",
                            "Content": text
                        })
            
            if not messages:
                print("⚠️ No messages found in channel.")
                return pd.DataFrame()
                
            return pd.DataFrame(messages)
            
        except SlackApiError as e:
            print(f"❌ Slack API Error: {e.response['error']}")
            return pd.DataFrame()
        except Exception as e:
            print(f"❌ Slack Handler Error: {e}")
            return pd.DataFrame()