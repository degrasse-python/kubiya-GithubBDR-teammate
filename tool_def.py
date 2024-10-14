import inspect

from kubiya_sdk import tool_registry
from kubiya_sdk.tools.models import Arg, Tool, FileSpec

from . import gituser

get_linkedin_email_from_github = Tool(
    name="get_linkedin_email_from_github",
    description="Generate csv data to be used for SalesOps",
    type="docker",
    image="python:3.11-bullseye",
    content="""
pip install requests slack_sdk litellm > /dev/null 2>&1

python /tmp/gituser.py --github_org_url "$github_org_url" --alert_subject "$alert_subject"
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
          name="github_org_url",
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
            destination="/tmp/gituser.py",
            source=inspect.getsource(gituser)
        )
    ]
)

# Register the updated tool
tool_registry.register("deonsaunders-kjr", get_linkedin_email_from_github)