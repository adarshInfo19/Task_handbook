import boto3
import json

s3=boto3.client("s3",region_name="ap-south-1");

def get_data_from_s3():
    print("inside the function of getting data from s3 ")


    bucket_name = "jsondatacollector"
    file_key="uploaded_data/employee_data.json"

    try:

        data = s3.get_object(Bucket=bucket_name,Key=file_key)

        file_content = data['Body'].read().decode('utf-8')

        json_data = json.loads(file_content)

        print('Data retrieved successfully ',json_data)

    except Exception as e:
        print("Error:",str(e))

get_data_from_s3()