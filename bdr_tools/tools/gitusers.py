import os
import csv
import re
import json
import time
from datetime import datetime, timedelta

import requests
import argparse
import pandas as pd
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

import pandas as pd
from bs4 import BeautifulSoup
from pydantic import BaseModel, Field, create_model
import html2text

from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

from openai import OpenAI
from langchain_ollama import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate

load_dotenv()


# Provide your personal access token to avoid API rate limits (optional but recommended)
GITHUB_TOKEN=os.environ.get('GITHUB_TOKEN')
GITHUB_HEADERS = {
    'Authorization': f'token {GITHUB_TOKEN}',
    'Accept': 'application/vnd.github.v3+json'
}
CSV='/tmp/git_signals.csv'

THREAD_TS = os.environ.get('SLACK_THREAD')
CHANNEL_ID = os.environ.get('SLACK_CHANNEL')
SLACK_TOKEN = os.environ.get('SLACK_API_TOKEN')
SUBJECT = os.environ.get('ALERT_SUBJECT')
OPENAI_API_KEY=os.environ.get('OPENAI_API_KEY')



SBR_WEBDRIVER=os.environ.get("SBR_WEBDRIVER")
OPENAI_API_KEY=os.environ.get('OPENAI_API_KEY')

model = OllamaLLM(model="llama3")

# Set up the Chrome WebDriver options
def setup_selenium():
  options = Options()

  # adding arguments
  options.add_argument("--disable-gpu")
  options.add_argument("--disable-dev-shm-usage")
  options.add_argument("--headless=new")
  
  # Randomize user-agent to mimic different users -- internet search for the user agent
  options.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.3")
  # Specify the path to the ChromeDriver
  service = Service(SBR_WEBDRIVER)  

  # Initialize the WebDriver
  driver = webdriver.Chrome(service=service, options=options)
  return driver

def fetch_html_selenium(url):
  driver = setup_selenium()
  try:
    driver.get(url)
    
    # Add random delays to mimic human behavior
    time.sleep(5)  # Adjust this to simulate time for user to read or interact
    
    # Add more realistic actions like scrolling
    # driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(3)  # Simulate time taken to scroll and read
    
    html = driver.page_source
    return html
  finally:
    driver.quit()

def clean_html(html_content):
  # extract_body_content by removing header and footer
  soup = BeautifulSoup(html_content, 'html.parser')
  
  # Remove headers and footers based on common HTML tags or classes
  for element in soup.find_all(['header', 'footer']):
    element.decompose()  # Remove these tags and their content

  return str(soup)


def html_to_markdown_with_readability(html_content):
  cleaned_html = clean_html(html_content)  
  
  # Convert to markdown
  markdown_converter = html2text.HTML2Text()
  markdown_converter.ignore_links = False
  markdown_content = markdown_converter.handle(cleaned_html)
  
  return markdown_content

# Define the pricing for gpt-4o-mini without Batch API
pricing = {
  "gpt-4o-mini": {
      "input": 0.150 / 1_000_000,  # $0.150 per 1M input tokens
      "output": 0.600 / 1_000_000, # $0.600 per 1M output tokens
  },
  "gpt-4o-2024-08-06": {
      "input": 2.5 / 1_000_000,  # $0.150 per 1M input tokens
      "output": 10 / 1_000_000, # $0.600 per 1M output tokens
  },
  # Add other models and their prices here if needed
  }

model_used='gpt-3.5-turbo' #"gpt-4o-mini"
    

def is_member_of_org(org, username):
  """Check if a user is a member of the given organization."""
  url = f"https://api.github.com/orgs/{org}/members/{username}"
  headers = {"Authorization": f"token {GITHUB_TOKEN}"}
  
  response = requests.get(url, headers=headers)
  
  # Status 204 means the user is a member, 404 means they are not
  return response.status_code == 204

def get_committers(repo_url, token=GITHUB_TOKEN):
  
  """ Get all the committers usernames from a Github org

  Args:
      repo_url (_type_): str - example: 'https://github.com/octocat/hello-world'

  Returns:
      _type_: list
  """ 

  # Extract owner and repo from the URL
  parts = repo_url.rstrip('/').split('/')
  owner, repo_name = parts[-2], parts[-1]

  # GitHub API endpoint for commits
  org_api_url = f"https://api.github.com/orgs/{owner}/"
  commits_api_url = f"https://api.github.com/repos/{owner}/{repo_name}/commits"
  
  # Calculate the timestamp for the past month
  one_month_ago = datetime.utcnow() - timedelta(days=30)
  since = one_month_ago.isoformat() + "Z"  # GitHub API requires the date in ISO 8601 format

  # Make the request to fetch commits
  headers = {"Authorization": f"token {token}"}
  response = requests.get(commits_api_url, params={"since": since}, headers=headers)
  
  if response.status_code != 200:
      print(f"Error: {response.status_code}, {response.json()}")
      return []
  else:
    print(response)
  # Extract unique committers
  columns = ["Name", 'Login',
             "Email", "Company", 
             "Url", "Blog", "Repo_Commited"]
  external_committers = pd.DataFrame(columns=columns)
  commits = response.json()
  for committer in commits:
    if is_member_of_org(org_api_url, committer['committer']['login']):
      continue
    # Extract unique committers
    else:

      user_data_dict = get_user_data(committer['committer']['url'], 
                                     repo_committed=repo_url)
      if user_data_dict.status_code == 403:
        break
      new_row = pd.DataFrame([user_data_dict])
      external_committers = pd.concat([external_committers, new_row], ignore_index=True)
  external_committers_unique = external_committers.drop_duplicates(subset='Name', keep='first')
  return external_committers_unique

def get_user_data(git_url,
                  headers={"Accept": "application/vnd.github.v3+json"},
                  repo_committed=None
                  ):
  user_data = requests.get(git_url,
                             headers=headers)
  

  if user_data.status_code != 200:
      print(f"Error: {user_data.status_code}, {user_data.json()}")
      return user_data.status_code
  else:
    user_dict = {"Name": str(user_data.json()['name']),
                  'Login': str(user_data.json()['login']),
                  "Company": str(user_data.json()['company']),
                  "Email": str(user_data.json()['email']),
                  "Url": str(user_data.json()['url']),
                  "Blog": str(user_data.json()['blog']),
                  "Repo_Commited": repo_committed}
    return user_dict

def get_user_linkedin(user,
                linkedin_url='None', 
                path=None,
                headers=None):
  """ Adds data to return csv for Github user.

  Args:
      user (_type_): str

  Returns:
      _type_: None
  """

  # USER_DATA
  # res[0]['login'] == username as str
  # res_user.json()['name']
  # res_user.json()['organizations_url']
  # res_user.json()['url']
  # res_user.json()['company']
  # res_user.json()['email']
  # res_user.json()['blog']

  try:
    # Scrape data
    raw_html = fetch_html_selenium(user)
    markdown = html_to_markdown_with_readability(raw_html)
    pattern = r'linkedin[^/]+/in/[^/]+'
    result = re.search(pattern, markdown)
    if result:
      linkedin_url = result[0]
      print(linkedin_url)


  except Exception as e:
    print(e)

  if headers:
    res = requests.get(user, 
                      headers=headers)
  else:
    res = requests.get(user)
  
  if path:
    with open(path, 'a', newline='') as file:
      # create headers
      writer = csv.writer(file, delimiter=',')
      writer.writerow([str(res.json()['name']),
                      str(res.json()['login']),
                      str(res.json()['company']),
                      str(res.json()['organizations_url']),
                      str(res.json()['email']),
                      str(res.json()['url']),
                      str(res.json()['blog']),
                      linkedin_url, 
                      ]
                    )
    file.close()
  else:
    with open('./user_data.csv', 'a', newline='') as file:
      # create headers
      writer = csv.writer(file, delimiter=',')
      writer.writerow([str(res.json()['name']),
                      str(res.json()['login']),
                      str(res.json()['company']),
                      str(res.json()['organizations_url']),
                      str(res.json()['email']),
                      str(res.json()['url']),
                      str(res.json()['blog']),
                      linkedin_url, 
                      ]
                    )
    file.close()


def send_user_data():
  return

def get_linkedin_url(markdown):
  pattern = r'linkedin[^/]+/in/[^/]+'
  result = re.search(pattern, markdown)
  print(result)
  return result[0]

def SaveExternalCommitersData(external_committers, path='./user_data.csv'):
  with open(path, 'a', newline='') as file:
    # create headers
      writer = csv.writer(file, delimiter=',')
      writer.writerow([ # str(res.json()['name']),
                       # str(res.json()['login']),
                       # str(res.json()['company']),
                       # str(res.json()['organizations_url']),
                       # str(res.json()['email']),
                       # str(res.json()['url']),
                       # str(res.json()['blog']),
                      ]
                    )
      
  file.close()

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

if __name__ == '__main__':
  # Example usage
  parser = argparse.ArgumentParser(description="Trigger a search for github users")
  parser.add_argument("--git_repo", required=True, help="The url of the git repo")
  args = parser.parse_args()

  git_repo = args.git_repo
  
  initial_comment = (f"Github Contrib CSV for Github Org '{git_repo}'")
  committers = get_committers(git_repo)
  for user in  committers.itertuples(index=True, name='Row'):
    print(f'api  url: {user.Url}')

    try:
      # Scrape data
      raw_html = fetch_html_selenium(user.Url)
      markdown = html_to_markdown_with_readability(raw_html)
      # path_to_data = scraper.save_raw_data(markdown, timestamp)
      print(f'-- markdown raw data -- ')
      print(f'... type: {type(markdown)}')
      print(f'... len : {len(markdown)}')
      print(markdown)
      linkedin_url = get_linkedin_url(markdown)
      if linkedin_url:
        print(linkedin_url)

    except Exception as e:
      print(e)
      linkedin_url='None'
    user_data = send_user_data(user['url'],
                            linkedin_url=linkedin_url, 
                            path=CSV,
                            headers=GITHUB_HEADERS)
  
  print("External users who committed in the last month:", committers)
  # Extract relevant information from the Slack response
  print(json.dumps(committers, indent=2))
