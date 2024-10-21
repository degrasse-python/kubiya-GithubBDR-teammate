
import os

from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

THREAD_TS = os.environ.get('SLACK_THREAD')
CHANNEL_ID = os.environ.get('SLACK_CHANNEL')
SLACK_TOKEN = os.environ.get('SLACK_API_TOKEN')
SUBJECT = os.environ.get('ALERT_SUBJECT')


def ExtractSlackResponseInfo(response):
  return {
      "ok": response.get("ok"),
      "file_id": response.get("file", {}).get("id"),
      "file_name": response.get("file", {}).get("name"),
      "file_url": response.get("file", {}).get("url_private"),
      "timestamp": response.get("file", {}).get("timestamp")
  }

def SendSlackFileToThread(token, 
                          channel_id, 
                          thread_ts, 
                          file_path, 
                          initial_comment):
    
  client = WebClient(token=token)
  try:
    response = client.files_upload_v2(
        channel=channel_id,
        file=file_path,
        initial_comment=initial_comment,
        thread_ts=thread_ts
    )
    return response
  except SlackApiError as e:
    print(f"Error sending file to Slack thread: {e}")
    raise
