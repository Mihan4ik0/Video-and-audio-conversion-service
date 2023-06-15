import boto3
from botocore.exceptions import ClientError

# Указание учетных данных для доступа к S3
access_key = "minioadmin"
secret_key = "minioadmin"

# Создание клиента S3 с указанием учетных данных
s3_client = boto3.client(
    "s3",
    endpoint_url="http://localhost:9000",
    aws_access_key_id=access_key,
    aws_secret_access_key=secret_key
)

def upload_file(file, bucket_name, key):
    with open(file, "rb") as f:
        s3_client.upload_fileobj(f, bucket_name, key)

def delete_file(bucket_name, key):
    s3_client.delete_object(Bucket=bucket_name, Key=key)

def check_file_exists(bucket_name, key):
    try:
        s3_client.head_object(Bucket=bucket_name, Key=key)
        return True
    except Exception as e:
        return False

def download_file(bucket_name, key, file_path):
    try:
        s3_client.download_file(bucket_name, key, file_path)
    except Exception as e:
        raise e
