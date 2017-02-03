import time, json, string, random
import os.path

from slackclient import SlackClient
import requests, boto3

slack_token = os.environ['SLACK_API_TOKEN']
aws_access_key_id =  os.environ['aws_access_key_id']
aws_secret_access_key os.environ['aws_secret_access_key']

sc = SlackClient(slack_token)

if sc.rtm_connect():
    while True:
        for event in sc.rtm_read():
            if event['type'] == 'file_created':
                slack_file_dets = sc.api_call(
                    'files.info',
                    file = event['file']['id'],
                    token = slack_token
                )

                download_url = slack_file_dets['file']['url_private']
                auth_value = 'Bearer %s' % slack_token
                headers = {'Authorization': auth_value}
                response = requests.get(download_url, headers=headers)

                filename = ''.join(random.choice(string.ascii_uppercase) for _ in range(6))
                extension = os.path.splitext(slack_file_dets['file']['name'])[1]
                image_filename = '%s%s' % (filename, extension)

                session = boto3.Session(aws_access_key_id=aws_access_key_id,
                                        aws_secret_access_key=aws_secret_access_key)
                s3 = session.resource("s3")

                data = response.content #open('t.png', 'rb')
                print s3.Bucket('lilscreenshare').put_object(Key=image_filename, Body=data)

                s3.Object('lilscreenshare', 'current.json').put(Body=json.dumps({'name': image_filename}))

        time.sleep(1)
else:
    print "Connection to Slack unavailable"