import boto3
import json
import os

dynamodb = boto3.client('dynamodb')
stepfunctions = boto3.client('stepfunctions')
table = os.getenv('TableName', '')

def lambda_handler(event, context):
    
    key={}
    taskoutput={}
    uri = event['path']
    findslash = uri.find('/', 1)
    id = uri[findslash+1:]
    print(f'Handling callback for {id}')
    key['URI'] = {'S': id} 
    result = dynamodb.get_item(TableName=table, Key=key)
    token = result['Item']['token']['S']
    stepfunctions.send_task_success(taskToken=token,output=json.dumps(taskoutput))
    
    return {
        'statusCode': 200,
        'body': json.dumps('Callback sent')
    }
