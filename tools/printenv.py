import os
import json 

from tools.utils import *

THREAD_TS = os.environ.get('SLACK_THREAD')
CHANNEL_ID = os.environ.get('SLACK_CHANNEL')
SLACK_TOKEN = os.environ.get('SLACK_API_TOKEN')
SUBJECT = os.environ.get('ALERT_SUBJECT')



# Example usage
initial_comment = (f"Getting all the envs for this teammate'")
# do something with the data
slack_response = SendSlackFileToThread(SLACK_TOKEN, 
                                        CHANNEL_ID, 
                                        THREAD_TS, 
                                        CSV, 
                                        initial_comment)

# Extract relevant information from the Slack response
response_info = ExtractSlackResponseInfo(slack_response)
print(json.dumps(response_info, indent=2))

for name, value in os.environ.items():
    print("{0}: {1}".format(name, value))


