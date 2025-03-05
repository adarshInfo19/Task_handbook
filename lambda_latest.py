import json
import boto3
import base64

s3 = boto3.client('s3')

BUCKET_NAME = 'jsondatacollector'
FILE_NAME = 'employee_data.json'

def lambda_handler(event, context):
    print("inside the lambda")
    try:
        body = event["body"]
        is_base64_encoded = event["isBase64Encoded"]

        file_content = base64.b64decode(body) if is_base64_encoded else body

        s3.put_object(Bucket=BUCKET_NAME, Key=FILE_NAME, Body=file_content ,ContentType="application/json")
        
        return {
            "statusCode": 200,
            "body": json.dumps({"message": "File uploaded to S3", "file_name": FILE_NAME})
        }

    except Exception as e:
        print(e)
        return {
            'statusCode': 400,
            'body': json.dumps('Error!')
        }