import boto3

def main():
    try:
        lambda_client = boto3.client('lambda')
        response = lambda_client.invoke(
            FunctionName = 'greytHR_to_S3',
            InvocationType = 'RequestResponse',
        )

        print('response after triggering lambda function ',response)
        
    except Exception as e:
        print(f"Main execution failed: {str(e)}")

if __name__ == "__main__":
    main()