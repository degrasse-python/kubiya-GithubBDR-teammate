import os
import csv
import re
import requests

GITHUB_URL="https://api.github.com/"
GITHUB_TOKEN=os.environ['GITHUB_TOKEN']
GITHUB_HEADERS = {
    'Authorization': f'token {GITHUB_TOKEN}',
    'Accept': 'application/vnd.github.v3+json'
}
CSV=os.environ['CSV_FILE_PATH']

with open(CSV, 'a+', newline='\n') as file:
  # create headers
  file.write('name,login,company,org_url,email,githublink,bloglink')
file.close()

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


def GetUserData(user_url, 
                path=None,
                headers=None):
  """ Iterates over a json to return csv of all user data

  Args:
      res_json (_type_): json

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
  if headers:
    res = requests.get(user_url, 
                      headers=headers)
  else:
    res = requests.get(user_url)
  
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
                      ]
                    )
    
    file.close()

  else:
    with open(CSV, 'w', newline='\n') as file:
      # create headers
      file.write('name,login,company,org_url,email,githublink,bloglink')




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

if __name__=='__main__':
  # grab the orgname from Github
  orgname = GrabOrgName('URL')
  # get the list of Repos for that org
  repo_json = GetOrgRepos(orgname)
  # get the users of each repo
  username_list = GetContribs(repo_json)
  # get the user data from the user list
  user_data = GetUserData(username_list)
