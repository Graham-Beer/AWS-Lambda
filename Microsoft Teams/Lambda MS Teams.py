import json
import logging
import os
import boto3
import datetime as dt
import accounts as acc

from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

# import environment variables
HOOK_URL = os.environ['HookUrl']
env_tags = os.environ['required_tags']

# set logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def filter_tags(client, env_tag_list):
    '''Function to filter tags from either an EC2 or RDS'''
    all_tags = list()
    for tag in client:
        if tag['Key'] in env_tag_list:
            all_tags.append(
                {"name": f"{tag['Key']}:", "value": f"{tag['Value']}"})
            env_tag_list.remove(tag['Key'])
    env_tag_list.sort()
    all_tags.sort(key=lambda x: x['name'])
    return env_tag_list, all_tags


def lambda_handler(event, context):

    logger.info("Event: " + str(event))
    message = json.loads(event['Records'][0]['Sns']['Message'])
    logger.info("Message: " + str(message))

    # Generic message variables
    account = message['account']
    region = message['region']
    time = message['time']

    if message['source'] == "aws.ec2":
        # EC2 message variables
        instance = message['detail']['instance-id']
        state = message['detail']['state']
        alarm_name = message['detail-type']

        # initialise boto3 to EC2
        ec2 = boto3.resource('ec2')
        client = ec2.Instance(instance).tags

        # Theme
        theme = {"themeColor": "64a837"}
        # Message test
        service_type = 'Instance ID'

    if message['source'] == "aws.rds":
        # Message variables
        instance = message['detail']['requestParameters']['dBInstanceIdentifier']
        state = message['detail']['responseElements']['dBInstanceStatus']
        alarm_name = 'RDS State-change Notification'

        # RDS ARN for tag instance
        rds_arn = message['detail']['responseElements']['dBInstanceArn']
        rds_instance = boto3.client('rds')
        rds_tags = rds_instance.list_tags_for_resource(ResourceName=f"{rds_arn}")
        client = rds_tags['TagList']

        # Theme
        theme = {"themeColor": "ffd700"}
        # Message test
        service_type = 'DB identifier'

    # Environment variable tag list
    env_tag_list = env_tags.replace("'", "").split(', ')
    # filter tags
    tag_list, all_tags = filter_tags(client, env_tag_list)

    # AWS accounts contained in 'accounts' module
    account_name = acc.accounts[account]

    # datetime formatting
    x = dt.datetime.strptime(time, '%Y-%m-%dT%H:%M:%SZ')
    formatted_dt = x.strftime('%a %b %d %Y %H:%M %p')

    # message message_data
    data = {
        "title": f"{alarm_name}",
        "text": " ",
        "sections": {
            "facts": all_tags
        }
    }
    # merge theme for service to message data
    message_data = {**data, **theme}

    # order displayed values
    message_data['sections']['facts'].insert(
        0, {"name": "Account ID:", "value": f"{account_name}"})
    message_data['sections']['facts'].insert(
        1, {"name": "Time:", "value": f"{formatted_dt}"})
    message_data['sections']['facts'].insert(
        2, {"name": "AWS Region:", "value": f"{region}"})
    message_data['sections']['facts'].insert(
        3, {"name": f"{service_type}:", "value": f"{instance}"})
    message_data['sections']['facts'].insert(
        4, {"name": "State:", "value": f"{state}"})
    message_data['sections']['facts'].append(
        {"name": "Missing Tags:", "value": f"{', '.join(tag_list)}"})

    # message information to display in Microsoft Teams
    teams_message = {
        "@context": "https://schema.org/extensions",
        "@type": "MessageCard",
        "themeColor": message_data['themeColor'],
        "title": message_data['title'],
        "text": message_data['text'],
        "sections": [
            message_data['sections']
        ]
    }

    # request connection to Microsoft Teams
    request = Request(
        HOOK_URL,
        json.dumps(teams_message).encode('utf-8'))

    # post message to Microsoft Teams
    try:
        response = urlopen(request)
        response.read()
        logger.info("Message posted")
    except HTTPError as err:
        logger.error(f"Request failed: {err.code} {err.reason}")
    except URLError as err:
        logger.error(f"Server connection failed: {err.reason}")
