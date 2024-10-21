import os
import json
from datetime import datetime, timedelta

import requests
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError


# Provide your personal access token to avoid API rate limits (optional but recommended)
GITHUB_URL="https://api.github.com/"
GITHUB_TOKEN=os.environ.get('GITHUB_TOKEN')
GITHUB_HEADERS = {
    'Authorization': f'token {GITHUB_TOKEN}',
    'Accept': 'application/vnd.github.v3+json'
}
GITHUB_REPO_URL=os.environ.get('GITHUB_ORG_URL')
CSV=os.environ['CSV_FILE_PATH']

THREAD_TS = os.environ.get('SLACK_THREAD')
CHANNEL_ID = os.environ.get('SLACK_CHANNEL')
SLACK_TOKEN = os.environ.get('SLACK_API_TOKEN')
SUBJECT = os.environ.get('ALERT_SUBJECT')
OPENAI_API_KEY=os.environ.get('OPENAI_API_KEY')




def is_member_of_org(org, username):
    """Check if a user is a member of the given organization."""
    url = f"https://api.github.com/orgs/{org}/members/{username}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    
    response = requests.get(url, headers=headers)
    
    # Status 204 means the user is a member, 404 means they are not
    return response.status_code == 204

def get_committers(repo_url):
    """Get unique committers from the past month, excluding organization members."""
    # Extract owner and repo from the URL
    parts = repo_url.rstrip('/').split('/')
    owner, repo = parts[-2], parts[-1]

    # GitHub API endpoint for commits
    api_url = f"https://api.github.com/repos/{owner}/{repo}/commits"
    
    # Calculate the timestamp for the past month
    since = (datetime.now() - timedelta(days=30)).isoformat()
    
    # Make the request to fetch commits
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    response = requests.get(api_url, params={"since": since}, headers=headers)
    
    if response.status_code != 200:
        print(f"Error: {response.status_code}, {response.json()}")
        return []

    # Extract unique committers
    commits = response.json()
    committers = {commit['author']['login'] for commit in commits if commit['author']}
    
    # Filter out committers who are part of the organization
    external_committers = [
        user for user in committers if not is_member_of_org(owner, user)
    ]
    
    return external_committers

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


# Example usage
repo_url = GITHUB_REPO_URL
initial_comment = (f"Github Contrib CSV for Github Org '{GITHUB_REPO_URL}'")
committers = get_committers(repo_url)
print("External users who committed in the last month:", committers)
# do something with the data
slack_response = SendSlackFileToThread(SLACK_TOKEN, 
                                        CHANNEL_ID, 
                                        THREAD_TS, 
                                        CSV, 
                                        initial_comment)

# Extract relevant information from the Slack response
response_info = ExtractSlackResponseInfo(slack_response)
print(json.dumps(response_info, indent=2))


