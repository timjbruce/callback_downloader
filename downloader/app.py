import boto3
import json
import os
import requests

sqs = boto3.client('sqs')
dynamodb = boto3.client('dynamodb')
filetable = os.getenv('FileTable', '')
callbackurl = os.getenv('CallbackUrl', '')

def lambda_handler(event, context):
    
    URI = event['name']
    ProjectId = event['projectid']
    
    #Perform GET against callback URL
    url = callbackurl + "?projectID="+ProjectId
    print(url)
    response = requests.get(url)
    print(response)
    
    #Gather all files and batch send to SQS or Dynamo
    responsejson = response.json()
    print(responsejson)
    item={}
    item['URI']={"S":URI}
    for file in responsejson['files']:
        item['FilenameURL']={"S":file}
        dynamodb.put_item(Item=item, TableName=filetable)

    return {
        'statusCode': 200,
        'body': {'Message':'Filenames saved for download'}
    }
