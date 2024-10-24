from pathlib import Path
import inspect

from kubiya_sdk import tool_registry
from kubiya_sdk.tools.models import Arg, Tool, FileSpec

from . import dummy_tool, printenv, gitusers


# Get the directory containing the script
script_dir = Path(__file__).parent.resolve()

# Create a Path object for the file
file_path = script_dir / "main.go"

dummy_tool = Tool(
    name="dummy-tool",
    description="This is a fake tool",
    type="docker",
    image="python:3.11-bullseye",
    args=[],
    secrets=[],
    env=[],
    content="""
    python /tmp/dummy_tool.py
    """,
    with_files=[
        FileSpec(
            destination="/tmp/dummy_tool.py",
            content=inspect.getsource(dummy_tool),
        ),
    ]
)

get_github_repo_commit_list = Tool(
    name="get_github_repo_commit_list",
    description="Get the Github repo commit Signals for repo",
    type="docker",
    image="python:3.11-bullseye",
    content="""
pip install pandas > /dev/null 2>&1
pip install argparse > /dev/null 2>&1
pip install slack_sdk > /dev/null 2>&1
pip install requests > /dev/null 2>&1
pip install bs4 > /dev/null 2>&1
pip install selenium > /dev/null 2>&1
pip install langchain_ollama > /dev/null 2>&1
pip install langchain_core > /dev/null 2>&1
pip install pydantic > /dev/null 2>&1
pip install html2text > /dev/null 2>&1
pip install litellm==1.49.5 > /dev/null 2>&1
pip install pillow==11.0.0 > /dev/null 2>&1
pip install tempfile > /dev/null 2>&1
sudo apt install wget
wget -nc https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb 
sudo apt update

sudo apt install -f ./google-chrome-stable_current_amd64.deb 

python /tmp/gitusers.py --git_repo $git_repo
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
          name="git_repo",
          type="str",
          description="URL of the Github Org to search",
          required=True
        ),
    ],
    with_files=[
        FileSpec(destination="/tmp/gitusers.py", content=inspect.getsource(gitusers)),
        #FileSpec(
         # destination="/tmp/requirements.txt",
          #content="slack-sdk==3.11.0\nrequests==2.32.3\nlitellm==1.49.5\npillow==11.0.0",
           #   )
    ]
)


printenv_tool = Tool(
    name="printenv_tool",
    description="Print your Environment variables",
    type="docker",
    image="python:3.11-bullseye",
    content="""
pip install argparse > /dev/null 2>&1
pip install slack_sdk > /dev/null 2>&1
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
      FileSpec(destination="/tmp/printenv.py", content=inspect.getsource(printenv)),

    ]
)

# Register the updated tool

tool_registry.register("deonsaunders-kjr", dummy_tool)
tool_registry.register("deonsaunders-kjr", get_github_repo_commit_list)
tool_registry.register("deonsaunders-kjr", printenv_tool)
