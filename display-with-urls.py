import json
import random
import string
import time
from os import environ
from os.path import splitext, basename
from urlparse import urlparse
import sys

import boto3
from botocore.exceptions import ClientError
import requests
from slackclient import SlackClient

'''
The logic in this script wires a slack channel to s3

The partner to this script simply displays the latest image_filename
(reading the values we update below in current.json)

Be sure to create settings.sh (from the example) and run it
before running this script,

$ source ./settings.sh
'''

aws_access_key_id = environ['AWS_ACCESS_KEY_ID']
aws_secret_access_key = environ['AWS_SECRET_ACCESS_KEY']
aws_bucket_name = environ['AWS_BUCKET_NAME']
slack_token = environ['SLACK_TOKEN']
slack_channel = environ['SLACK_CHANNEL']

# Possible values for screens. config this.
screens = ['racehorse', 'icecream', 'strawberry', 'pepper', 'balloon', 'banana', 'blowfish']
# the screen where an image will appear when it's first posted
default_screen = screens[0]


def main():
    existing_status = get_start_state()
    # Our connection to the Slack API
    sc = SlackClient(slack_token)
    if sc.rtm_connect():
        while True:
            existing_status = build_config(existing_status, sc)
            time.sleep(1)
    else:
        print("Connection to Slack unavailable")


def get_start_state():
    """ Get current.json from the S3 bucket """
    s3 = s3_connect()
    try:
        s3.Bucket(aws_bucket_name).download_file('current.json', 'current.json')
    except ClientError as e:
        if e.response['Error']['Code'] == "404":
            sys.exit("current.json does not exist -- stopping")
        else:
            raise
    with open('current.json', 'r') as json_file:
        data = json.load(json_file)
    return data


def s3_connect():
    """ Connect to S3 and return the session resource """
    session = boto3.Session(aws_access_key_id=aws_access_key_id,
                            aws_secret_access_key=aws_secret_access_key)
    return session.resource("s3")


def post_image_to_aws(image_url, filename, file_ext, held_by_slack=False):
    """ Put an image in an S3 bucket """

    # Slack headers
    slack_request_headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_5) AppleWebKit/537.36 '
                                           '(KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36'}
    auth_value = 'Bearer %s' % slack_token
    slack_request_headers['Authorization'] = auth_value

    if held_by_slack:
        response = requests.get(image_url, headers=slack_request_headers)
    else:
        response = requests.get(image_url)

    data = response.content

    image_filename = '%s%s' % (filename, file_ext)

    # post image with new filename to s3
    s3 = s3_connect()
    s3.Bucket(aws_bucket_name).put_object(Key=image_filename, Body=data)

    return image_filename


def update_current(generated_status):
    """ Write current.json to the S3 bucket """
    s3 = s3_connect()
    s3.Object(aws_bucket_name, 'current.json').put(Body=json.dumps(generated_status), CacheControl='max-age=1')


def extract_destinations(obj):
    """ Get reactions aka emoji from a Slack message or file """
    destinations = []
    if 'reactions' in obj.keys():
        for reaction in obj['reactions']:
            if reaction['name'] in screens:
                destinations.append(reaction['name'])
    if not destinations:
        destinations = [default_screen]
    return destinations


def generate_filename(status):
    """ Create a random filename -- don't collide with recent filenames """
    existing = [x.split('.')[0] for x in status['_mapping'].values()]
    while (True):
        filename = ''.join(random.choice(string.ascii_uppercase) for _ in range(6))
        if filename not in existing:
            return filename


def update_status(destinations, existing_status, generated_status, slack_image_id, url, held_by_slack):
    """ Upload image to S3 if necessary, then update the generated status """
    url_pieces = urlparse(url)
    file_ext = splitext(basename(url_pieces.path))[1]
    not_uploaded = True
    image_filename = None
    if slack_image_id in existing_status['_mapping']:
        image_filename = existing_status['_mapping'][slack_image_id]
        s3 = s3_connect()
        try:
            s3.Object(aws_bucket_name, image_filename).load()
            not_uploaded = False
        except ClientError as e:
            if e.response['Error']['Code'] == "404":
                not_uploaded = True
            else:
                raise
    if not_uploaded:
        print("uploading to bucket...")
        filename = generate_filename(existing_status)
        image_filename = post_image_to_aws(url, filename, file_ext, held_by_slack=held_by_slack)
        existing_status['_mapping'][slack_image_id] = image_filename
    for destination in destinations:
        generated_status[destination] = {'id': slack_image_id, 'url': image_filename}
    generated_status['_mapping'] = existing_status['_mapping']
    return generated_status


def build_config(existing_status, sc):
    """

    Our destinations will be bundled in a json object that kinda looks like
    this (and is the thing watched by the js, current.js, in the screen's
    browser to see if it needs to update its pic)

    {
    'racehorse': { 'url': 'http:// bucket at s3'},
                    'id': 'some slack generated guid',
                    'bg': '#fff'},

    'icecream':  { 'url': 'http:// bucket at s3'},
                    'id': 'some slack generated guid',
                    'bg': '#000'},
    }
    """

    generated_status = {}
    # retrieve recent posts in our channel
    history = sc.api_call('channels.history', channel=slack_channel, inclusive='true', count=len(screens))

    # find images posted to channel and build status to update
    # probably not great to rely on order like this:
    messages = history['messages']
    messages.reverse()
    for kl in messages:
        if 'ts' in kl:
            slack_image_id = kl['ts']
            # uploaded image
            if 'file' in kl.keys() and 'url_private' in kl['file'].keys():
                # see if we have reactions along with our uploaded file
                destinations = extract_destinations(kl['file'])
                url = kl['file']['url_private']
                generated_status = update_status(destinations, existing_status, generated_status, slack_image_id,
                                                 url, held_by_slack=True)

            # if someone pastes text with a link to an image in it
            elif 'attachments' in kl.keys() and 'image_url' in kl['attachments'][0].keys():
                destinations = extract_destinations(kl)
                url = kl['attachments'][0]['image_url']
                generated_status = update_status(destinations, existing_status, generated_status, slack_image_id,
                                                 url, held_by_slack=False)

    if generated_status:
        update_current(generated_status)
        existing_status = generated_status

    return existing_status


if __name__ == "__main__":
    main()
