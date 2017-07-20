from os import environ
from os.path import splitext, basename
import time, json, string, random
from urlparse import urlparse

from slackclient import SlackClient
import requests, boto3


'''
The logic in this script wires a slack channel to s3

The partner to this script simply displays the latest image_filename
(reading the values we update below in current.json)

Be sure to create settings.sh (from the example) and run it
before running this script,

$source ./settings.sh
'''


aws_access_key_id =  environ['aws_access_key_id']
aws_secret_access_key = environ['aws_secret_access_key']
aws_bucket_name = environ['aws_bucket_name']
slack_token = environ['slack_token']
slack_channel = environ['slack_channel']


def post_image_to_aws(image_url, file_ext, held_by_slack=False):
    # if we have an image url, create a file name, update our pointer file,
    # current.json, and put the image on s3

    # Slack headers
    slack_request_headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36'}
    auth_value = 'Bearer %s' % slack_token
    slack_request_headers['Authorization'] = auth_value

    if held_by_slack:
        response = requests.get(image_url, headers=slack_request_headers)
    else:
        response = requests.get(image_url)

    data = response.content

    # create a rando filename
    filename = ''.join(random.choice(string.ascii_uppercase) for _ in range(6))
    image_filename = '%s%s' % (filename, file_ext)

    # post image with new filename to s3
    session = boto3.Session(aws_access_key_id=aws_access_key_id,
                            aws_secret_access_key=aws_secret_access_key)
    s3 = session.resource("s3")
    s3.Bucket(aws_bucket_name).put_object(Key=image_filename, Body=data)

    return image_filename

def update_current(generated_status):
    # if we have an image url, create a file name, update our pointer file,
    # current.json, and put the image on s3

        session = boto3.Session(aws_access_key_id=aws_access_key_id,
                        aws_secret_access_key=aws_secret_access_key)
        s3 = session.resource("s3")
        s3.Object(aws_bucket_name, 'current.json').put(Body=json.dumps(generated_status), CacheControl='max-age=1')


def build_config():
    # Possible values for screens. config this.
    destinations = ['racehorse', 'icecream', 'strawberry', 'pepper', 'balloon', 'banana', 'blowfish']

    # the screen where an image will appear when it's first posted
    default_screen = destinations[0]

    # Our destinations will be bundled in a json object that kinda looks like
    # this (and is the thing watched by the js, current.js, in the screen's
    # browser to see if it needs to update it's pic)

    '''
    {
    'racehorse': { 'url': 'http:// bucket at s3'},
                    'id': 'some slack generated guid',
                    'bg': '#fff'},

    'icecream':  { 'url': 'http:// bucket at s3'},
                    'id': 'some slack generated guid',
                    'bg': '#000'},
    }
    '''

    print "building config"

    # Keep track of our existing status so that we only generate
    # a new current.json file if we have a change
    existing_status = {}

    # Our connection to the Slack API
    sc = SlackClient(slack_token)

    if sc.rtm_connect():
        while True:
            generated_status = {}

            for event in sc.rtm_read():
                # retrieve recent posts in our channel
                history = sc.api_call('channels.history', channel=slack_channel, inclusive='true', count=len(destinations))

                # find images posted to channel and build status to update
                for kl in history['messages']:
                    # uploaded image
                    if 'file' in kl.keys() and 'url_private' in kl['file'].keys():
                        # see if we have reactions along with our uploaded file
                        if 'reactions' in kl['file'].keys():
                            for reaction in kl['file']['reactions']:
                                if reaction['name'] in destinations:
                                    destination = reaction['name']
                        else:
                            destination = default_screen

                        url = kl['file']['url_private']
                        slack_image_id = kl['ts']

                        if destination not in existing_status.keys() or existing_status[destination]['id'] != slack_image_id:
                            url_pieces = urlparse(url)
                            file_ext = splitext(basename(url_pieces.path))[1]
                            image_filename = post_image_to_aws(url, file_ext, held_by_slack=True)
                            new_dest = {destination: {'id': slack_image_id, 'url': image_filename}}
                            generated_status.update(new_dest)


                    # if someone pastes text with a link to an image in it
                    if 'attachments' in kl.keys() and 'image_url' in kl['attachments'][0].keys():
                        if 'reactions' in kl.keys():
                            for reaction in kl['reactions']:
                                if reaction['name'] in destinations:
                                    destination = reaction['name']
                        else:
                            destination = default_screen

                        url = kl['attachments'][0]['image_url']
                        slack_image_id = kl['ts']

                        if destination not in existing_status.keys() or existing_status[destination]['id'] != slack_image_id:
                            url_pieces = urlparse(url)
                            file_ext = splitext(basename(url_pieces.path))[1]
                            image_filename = post_image_to_aws(url, file_ext)
                            new_dest = {destination: {'id': slack_image_id, 'url': image_filename}}
                            generated_status.update(new_dest)


                delta_exists = False
                for dest in generated_status:
                    if dest not in existing_status.keys():
                        delta_exists = True
                    elif generated_status[dest]['id'] != existing_status[dest]['id']:
                        delta_exists = True

                if delta_exists:
                    update_current(generated_status)
                    existing_status = generated_status

                time.sleep(1)


    else:
        print "Connection to Slack unavailable"

build_config()
