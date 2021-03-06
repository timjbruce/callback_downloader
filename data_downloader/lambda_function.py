import json
import boto3
import os
import requests
import sys

region = os.getenv('Region', '')
dynamodb = boto3.client('dynamodb', region_name=region)
filetable = os.getenv('FileTable', '')
s3 = boto3.client('s3', region_name=region)
bucket = os.getenv('Bucket','')

def lambda_handler(event, context):

    URI = event['name']

    keyconditionexpression = 'URI = :val1'
    expressionattributevalues = {':val1':{"S":URI}}
    print(expressionattributevalues)
    files = dynamodb.query(TableName=filetable, Limit=100,
        KeyConditionExpression=keyconditionexpression,
        ExpressionAttributeValues=expressionattributevalues)
    print(files)
    for file in files['Items']:
        shortfile = file['FilenameURL']['S'][file['FilenameURL']['S'].rfind('/')+1:]
        fullfile = '/tmp/' + shortfile
        response = requests.get(file['FilenameURL']['S'])
        if response.status_code == 200:
            open(fullfile, 'wb').write(response.content)
            s3.put_object(Body=fullfile, Bucket=bucket, Key=URI + "/" + shortfile)
            #could delete files from dynamodb

    return {
        "statusCode": 200,
        "body": ""
    }
    
def container_start(argv):
    #create an event and context that is like that passed in from Step Functions
    #to Lambda or SQS to Lambda (future model).
    print('started container')
    event = {}
    context = {}
    event['name']=str(argv)
    #call lambda_handler
    print('calling download function with : ')
    print(event)
    response = lambda_handler(event, context)
    return response

if __name__=="__main__":
    print('arguments in order')
    for arg in sys.argv:
        print(arg)
    container_start(sys.argv[len(sys.argv)-1])