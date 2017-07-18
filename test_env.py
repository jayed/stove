from os import environ
import json

import requests
from slackclient import SlackClient


''' This script will test the Stove environment vars
and connection to slack by printing the list of
slack channels associated with the given slack credentials
'''

slack_token = environ['slack_token']
aws_access_key_id =  environ['aws_access_key_id']
aws_secret_access_key = environ['aws_secret_access_key']
slack_channel = environ['slack_channel']


sc = SlackClient(slack_token)

if sc.rtm_connect():
    while True:
        for event in sc.rtm_read():
            # retrieve channel list
            history = sc.api_call('channels.list', exclude_members=1)

            print json.dumps(history, sort_keys=True, indent=4, separators=(',', ': '))
else:
    print "Connection to Slack unavailable"
