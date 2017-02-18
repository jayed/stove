import time, json, string, random
from os import path, environ
from os.path import splitext, basename
from urlparse import urlparse

from slackclient import SlackClient
import requests, boto3


'''
The logic below wires a slack channel to s3

The partner to this script simply displays the latest image_filename
(reading the values we update below in current.json)
'''


def post_image_to_aws(image_url, file_ext, headers):
        # if we have an image url, create a file name, update our pointer file,
        # current.json, and put the image on s3
        print "new %s image detected, %s" % (file_ext, image_url)

        response = requests.get(image_url, headers=headers)
        data = response.content

        # create a rando filename
        filename = ''.join(random.choice(string.ascii_uppercase) for _ in range(6))
        image_filename = '%s%s' % (filename, file_ext)

        session = boto3.Session(aws_access_key_id=aws_access_key_id,
                                aws_secret_access_key=aws_secret_access_key)
        s3 = session.resource("s3")
        s3.Bucket('lilscreenshare').put_object(Key=image_filename, Body=data)
        s3.Object('lilscreenshare', 'current.json').put(Body=json.dumps({'name': image_filename}))



# Grab our vars from the env
slack_token = environ['slack_token']
aws_access_key_id =  environ['aws_access_key_id']
aws_secret_access_key = environ['aws_secret_access_key']
slack_channel = environ['slack_channel']


# everything we do happens through our slack clent object
sc = SlackClient(slack_token)

if sc.rtm_connect():
    while True:
        for event in sc.rtm_read():
            if 'channel' in event.keys() and event['channel'] == slack_channel:
                

                # The two values we're intereted in finding
                image_url = ''
                file_ext = ''

                headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36'}

                if 'subtype' in event and (event['subtype'] == 'file_created' or event['subtype'] == 'file_share'):
                    # if someone uploads a file to slack
                    slack_file_dets = sc.api_call(
                        'files.info',
                        file = event['file']['id'],
                        token = slack_token
                    )

                    image_url = slack_file_dets['file']['url_private']
                    file_ext = splitext(slack_file_dets['file']['name'])[1]

                    auth_value = 'Bearer %s' % slack_token
                    headers['Authorization'] = auth_value

                    post_image_to_aws(image_url, file_ext, headers)

                if event['type'] == 'message' and 'message' in event.keys() and 'attachments' in event['message'].keys() and 'image_url' in event['message']['attachments'][0].keys():
                    # if someone pastes text with a link to an image in it
                    image_url = event['message']['attachments'][0]['image_url']
                    url_pieces = urlparse(image_url)
                    file_ext = splitext(basename(url_pieces.path))[1]

                    post_image_to_aws(image_url, file_ext, headers)


            time.sleep(1)
else:
    print "Connection to Slack unavailable"