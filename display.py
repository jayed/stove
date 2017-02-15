import time, json, string, random
from os import path, environ

from slackclient import SlackClient
import requests, boto3


'''
The logic below wires a slack channel to s3

The partner to this script simply displays the latest image_filename
(reading the values we update below in current.json)
'''

slack_token = environ['slack_token']
aws_access_key_id =  environ['aws_access_key_id']
aws_secret_access_key = environ['aws_secret_access_key']

sc = SlackClient(slack_token)

if sc.rtm_connect():
    while True:
        for event in sc.rtm_read():


            if event['type'] == 'file_created' or event['type'] == 'file_shared':
                # if we receive a file upload
                slack_file_dets = sc.api_call(
                    'files.info',
                    file = event['file']['id'],
                    token = slack_token
                )

                channel = slack_file_dets['file']['channels'][0]

                if channel == 'C40UJH0CV':
                    download_url = slack_file_dets['file']['url_private']
                    print "new image detected, %s" % download_url

                    auth_value = 'Bearer %s' % slack_token
                    headers = {'Authorization': auth_value}
                    response = requests.get(download_url, headers=headers)

                    filename = ''.join(random.choice(string.ascii_uppercase) for _ in range(6))
                    extension = path.splitext(slack_file_dets['file']['name'])[1]
                    image_filename = '%s%s' % (filename, extension)

                    session = boto3.Session(aws_access_key_id=aws_access_key_id,
                                            aws_secret_access_key=aws_secret_access_key)
                    s3 = session.resource("s3")

                    data = response.content
                    s3.Bucket('lilscreenshare').put_object(Key=image_filename, Body=data)

                    s3.Object('lilscreenshare', 'current.json').put(Body=json.dumps({'name': image_filename}))

        time.sleep(1)
else:
    print "Connection to Slack unavailable"