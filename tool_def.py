import inspect

from kubiya_sdk import tool_registry
from kubiya_sdk.tools.models import Arg, Tool, FileSpec

from . import gitusers

get_github_repo_commit_list = Tool(
    name="get_github_repo_commit_list",
    description="Generate csv data to be used for SalesOps",
    type="docker",
    image="python:3.11-bullseye",
    content="""
pip install requests slack_sdk litellm > /dev/null 2>&1

python /tmp/gitusers.py --github_repo_url "$github_repo_url" --alert_subject "$alert_subject"
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
        Arg(
          name="alert_subject",
          type="str",
          description="Subject of the alert, used to filter relevant panels",
          required=True
        )
    ],
    with_files=[
        FileSpec(
            destination="/tmp/gitusers.py",
            source=inspect.getsource(gitusers)
        )
    ]
)

# Register the updated tool
tool_registry.register("deonsaunders-kjr", get_github_repo_commit_list)