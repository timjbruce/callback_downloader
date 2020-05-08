import boto3
import json
import os

dynamodb = boto3.client('dynamodb')
table = os.getenv('TableName','')

def lambda_handler(event, context):
    
    print(f'Storing token {event["token"]} for {event["projectid"]}')
    
    item={}
    item['URI'] = {"S":event['uri']}
    item['ProjectId'] = {"S":event['projectid']}
    item['token']={"S":event['token']}

    dynamodb.put_item(TableName=table, Item=item)

    return {
        'statusCode': 200,
        'body': json.dumps('Waiting for callback')
    }

