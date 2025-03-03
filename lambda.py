# deploy this below code to the aws lambda

import json
import boto3

s3 = boto3.client('s3')

FILE_NAME = 'employee_data.json'
S3_KEY = 'uploaded_data/employee_data.json'
BUCKET_NAME = 'jsondatacollector'

def lambda_handler(event, context):
    

    try:
        # Upload file to S3
        s3.upload_file(FILE_NAME, BUCKET_NAME, S3_KEY)
        
        return {
            "statusCode": 200,
            "body": f"File {FILE_NAME} uploaded successfully to {BUCKET_NAME}/{S3_KEY}"
        }
    except Exception as e:
        return {
            "statusCode": 500,
            "body": f"Error uploading file: {str(e)}"
        }