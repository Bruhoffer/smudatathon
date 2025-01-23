import boto3

def test_bucket_access(bucket_name):
    s3 = boto3.client('s3')
    try:
        s3.head_bucket(Bucket=bucket_name)
        print(f"Access to bucket '{bucket_name}' is allowed.")
    except Exception as e:
        print(f"Access to bucket '{bucket_name}' denied: {e}")

# Replace with possible bucket names
test_bucket_access("smudatathon-textract-bucket")
