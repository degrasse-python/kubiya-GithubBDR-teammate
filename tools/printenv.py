import os
import json 

from tools.utils import *

THREAD_TS = os.environ.get('SLACK_THREAD')
CHANNEL_ID = os.environ.get('SLACK_CHANNEL')
SLACK_TOKEN = os.environ.get('SLACK_API_TOKEN')


# Example usage
initial_comment = (f"Getting all the envs for this teammate'")
# do something with the data

for name, value in os.environ.items():
    print("{0}: {1}".format(name, value))


