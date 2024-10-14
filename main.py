import os
from typing import List
import re
import requests

from fastapi import (FastAPI,
                     Request)
from pydantic import BaseModel



# globals
GITHUB_URL="https://api.github.com/"
LINKEDIN_URL=''
HOST=r'http://localhost:8000'
CLIENT=[]

GITHUB_API_TOKEN=os.environ['GITHUB_API_TOKEN']
LINKEDIN_API_TOKEN=os.environ['LINKEDIN_API_TOKEN']

# create api
app = FastAPI()

# data model
class Github(BaseModel):
  
  # declare data expected by body
  # latitude: float
  # longitude: float
  # start: str
  end: str

@app.get("/")
def read_root():
  return "Hello World"

@app.post("/addToList")
def post_to_list():
  return "This function will add a github org to the list of orgs on the backend"


def GrabOrgName(github_org_url):
  """ Grab the org name from the URL given at prompt.

  Args:
      github_org_url (_type_): str
  """
  pattern = '^https?://[^/]+(/[^?#]*)?'
  result = re.match(pattern, github_org_url)
  return result.groups()[0]


def GetOrgRepos(org_name):
  """ Get all the repos from an organization

  Args:
      org_name (_type_): str

  Returns:
      _type_: json
  """  

  repos_uri = GITHUB_URL + 'orgs' + org_name + '/repos'

  return requests.get(repos_uri).json()


def GetContribs(repos_json):
  """ Get all the contributors usernames from a Github org

  Args:
      repo_list (_type_): json

  Returns:
      _type_: json
  """  
  for repo in repos_json:
    #  res_repos.json()[0]['full_name'] == repo name
    full_name = repo['full_name']
    repos_uri = GITHUB_URL + 'repos/' + full_name + 'contributors'  
    res_contrib_list = requests.get(repos_uri).json()


  return requests.get(repos_uri).json()


def GetUserData(res_json):
  """ Iterates over a json to return csv of all user data

  Args:
      res_json (_type_): json

  Returns:
      _type_: <response ###> object
  """


    #
  # USER_DATA
  # res[0]['login'] == username as str
  # res_user.json()['name']
  # res_user.json()['company']
  # res_user.json()['email']
  # res_user.json()['blog']
   
  repos_uri = GITHUB_URL + res_json[0]['login']
  res = requests.get()

  for url in urls:
    res_user = requests.get(url)
    print(res_user.json()['company'])
      
    if 'linkedin' in res_user.json()['blog']:
      print(res_user.json()['blog'])
      print('Has linkedin')
    else:
      print(res_user.json())
  
  return res


if __name__=='__main__':
  # grab the orgname from Github
  orgname = GrabOrgName('URL')
  # get the list of Repos for that org
  repo_json = GetOrgRepos(orgname)
  # get the users of each repo
  username_list = GetContribs(repo_json)
  # get the user data from the user list
  user_data = GetUserData(username_list)
