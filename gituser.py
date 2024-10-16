import os
from datetime import datetime
import csv
from typing import List
import re
import json

import requests
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

import scraper


GITHUB_URL="https://api.github.com/"
GITHUB_TOKEN=os.environ.get('GITHUB_TOKEN')
GITHUB_HEADERS = {
    'Authorization': f'token {GITHUB_TOKEN}',
    'Accept': 'application/vnd.github.v3+json'
}
GITHUB_ORG_URL=os.environ.get('GITHUB_ORG_URL')
CSV=os.environ['CSV_FILE_PATH']

THREAD_TS = os.environ.get('SLACK_THREAD')
CHANNEL_ID = os.environ.get('SLACK_CHANNEL')
SLACK_TOKEN = os.environ.get('SLACK_API_TOKEN')
SUBJECT = os.environ.get('ALERT_SUBJECT')

with open(CSV, 'a+', newline='\n') as file:
  # create headers
  file.write('name,login,company,org_url,email,githublink,bloglink')
file.close()

# functions
def GrabOrgName(github_org_url,
                headers=None):
  """ Grab the org name from the URL given at prompt.

  Args:
      github_org_url (_type_): str
  """
  pattern = '^https?://[^/]+(/[^?#]*)?'
  result = re.match(pattern, github_org_url)
  return result.groups()[0]


def GetOrgRepos(org_name,
                headers=None):
  """ Get all the repos from an organization

  Args:
      org_name (_type_): str

  Returns:
      _type_: json
  """  

  repos_uri = GITHUB_URL + 'orgs' + org_name + '/repos'

  return requests.get(repos_uri).json()



def GetUserData(user,
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
    raw_html = scraper.fetch_html_selenium(user)
    markdown = scraper.html_to_markdown_with_readability(raw_html)
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


def GetAllContribsData(repos_json,
                headers=None):
  """ Get all the contributors usernames from a Github org

  Args:
      repo_list (_type_): json

  Returns:
      _type_: json
  """  
  if headers:
    # for each repo get all contributors
    for repo in repos_json:
      repo_contrib_uri = repo['url'] + '/contributors' 
      res_contrib_list = requests.get(repo_contrib_uri, headers=headers).json()

      for user in res_contrib_list:
        print(user)
        user_data = GetUserData(user['url'], 
                                path=CSV)
  else:
    for repo in repos_json:
      repo_contrib_uri = repo['url'] + '/contributors' 
      res_contrib_list = requests.get(repo_contrib_uri).json()

      for user in res_contrib_list:
        print(user)
        user_data = GetUserData(user['url'], 
                                path=CSV)


def GetAllContribsData(repos_json,
                headers=None):
  """ Get all the contributors usernames from a Github org

  Args:
      repo_list (_type_): json

  Returns:
      _type_: json
  """  
  if headers:
    # for each repo get all contributors
    for repo in repos_json:
      repo_contrib_uri = repo['url'] + '/contributors' 
      res_contrib_list = requests.get(repo_contrib_uri, headers=headers).json()

      for user in res_contrib_list:
        print(user)
        user_data = GetUserData(user['url'], 
                                path=CSV)
  else:
    for repo in repos_json:
      repo_contrib_uri = repo['url'] + '/contributors' 
      res_contrib_list = requests.get(repo_contrib_uri).json()

      for user in res_contrib_list:
        print(user)
        user_data = GetUserData(user['url'], 
                                path=CSV)


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


def ExtractSlackResponseInfo(response):
    return {
        "ok": response.get("ok"),
        "file_id": response.get("file", {}).get("id"),
        "file_name": response.get("file", {}).get("name"),
        "file_url": response.get("file", {}).get("url_private"),
        "timestamp": response.get("file", {}).get("timestamp")
    }


if __name__=='__main__':
  # grab the orgname from Github
  orgname = GrabOrgName(GITHUB_ORG_URL)
  # get the list of Repos for that org
  repo_json = GetOrgRepos(orgname)
  # get the users of each repo
  initial_comment = (f"Github Contrib CSV for Github Org '{GITHUB_ORG_URL}'")
  GetAllContribsData(repo_json)
  # do something with the data
  slack_response = SendSlackFileToThread(SLACK_TOKEN, 
                                         CHANNEL_ID, 
                                         THREAD_TS, 
                                         CSV, 
                                         initial_comment)

  # Extract relevant information from the Slack response
  response_info = ExtractSlackResponseInfo(slack_response)
  print(json.dumps(response_info, indent=2))
