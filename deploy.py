import sys
import os

sys.path.append(os.path.join(os.getcwd(), 'dependencies'))

import boto3

session = boto3.Session(
    aws_access_key_id=os.environ['ROBOT_AWS_ACCESS_KEY_ID'],
    aws_secret_access_key=os.environ['ROBOT_AWS_SECRET_ACCESS_KEY'],
)

lambda_client = session.client('lambda')

for i in range(100):
    print('creating function number ', i)
    lambda_client.create_function(
        FunctionName='show-machine-ip-' + str(i),
        Runtime='python3.6',
        Role='arn:aws:iam::833792831349:role/lambda_basic_execution',
        Handler='ip.handler',
        Code={
            'S3Bucket': 'recaptcha-spider-browser',
            'S3Key': 'ip.zip'
        },
        Description='',
        Timeout=15,
        MemorySize=128,
        Publish=False,
        Environment={
            'Variables': {
                'ROBOT_AWS_ACCESS_KEY_ID': 'AKIAJVEXA6CU6YU4D34Q',
                'ROBOT_AWS_SECRET_ACCESS_KEY': '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'
            }
        },
    )