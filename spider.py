import sys
import os
import asyncio

sys.path.append(os.path.join(os.getcwd(), 'dependencies'))

import boto3
import urllib3
from bypass import ByPass
from raven.contrib.awslambda import LambdaClient

urllib3.disable_warnings()
client = LambdaClient(os.environ['SENTRY_AUTH_URL'])


@client.capture_exceptions
def handler(event, context):
    session = boto3.Session(
        aws_access_key_id=os.environ['ROBOT_AWS_ACCESS_KEY_ID'],
        aws_secret_access_key=os.environ['ROBOT_AWS_SECRET_ACCESS_KEY'],
    )

    async def main():
        bypass = ByPass(session)
        page = await bypass.setUp()

        await page.goto('https://www.google.com/recaptcha/api2/demo')
        await bypass.run()
        await bypass.print_and_screenshot()

    asyncio.get_event_loop().run_until_complete(main())


if os.environ['DEBUG'] == 'y':
    handler(None, None)
