import inspect

from kubiya_sdk import tool_registry
from kubiya_sdk.tools.models import Arg, Tool, FileSpec

import tools.gitusers as gitusers
import tools.printenv as printenv

get_github_repo_commit_list = Tool(
    name="get_github_repo_commit_list",
    description="Generate csv data to be used for SalesOps",
    type="docker",
    image="python:3.11-bullseye",
    content="""
pip install slack_sdk > /dev/null 2>&1
pip install argparse > /dev/null 2>&1
pip install requests > /dev/null 2>&1
pip install litellm==1.49.5 > /dev/null 2>&1
pip install pillow==11.0.0 > /dev/null 2>&1
pip install tempfile > /dev/null 2>&1
python /tmp/gitusers.py --github_repo_url "$github_repo_url"
      """,
    secrets=[
        "GITHUB_TOKEN", 
        "SLACK_API_TOKEN", 
    ],
    env=[
        "SLACK_THREAD_TS", 
        "SLACK_CHANNEL_ID"
    ],
    args=[
        Arg(
          name="github_repo_url",
          type="str",
          description="URL of the Github Org to search",
          required=True
        ),
    ],
    with_files=[
        #FileSpec(destination="/tmp/gitusers.py",source=inspect.getsource(gitusers)),
        FileSpec(
          destination="/tmp/requirements.txt",
          content="slack-sdk==3.11.0\nrequests==2.32.3\nlitellm==1.49.5\npillow==11.0.0",
              )
    ]
)



printenv = Tool(
    name="printenv",
    description="Print Env variables",
    type="docker",
    image="python:3.11-bullseye",
    content="""
pip install slack_sdk > /dev/null 2>&1
pip install argparse > /dev/null 2>&1
pip install requests > /dev/null 2>&1
pip install litellm==1.49.5 > /dev/null 2>&1
pip install pillow==11.0.0 > /dev/null 2>&1
pip install tempfile > /dev/null 2>&1
python /tmp/printenv.py
      """,
    secrets=[
        "SLACK_API_TOKEN", 
    ],
    env=[
        "SLACK_THREAD_TS", 
        "SLACK_CHANNEL_ID"
    ],
    args=[
          ],
    with_files=[
      FileSpec(destination="/tmp/gitusers.py",source=inspect.getsource(gitusers)),

    ]
)

# Register the updated tool
tool_registry.register("deonsaunders-kjr", get_github_repo_commit_list)
tool_registry.register("deonsaunders-kjr", printenv)
