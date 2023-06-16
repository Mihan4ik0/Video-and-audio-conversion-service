import boto3
from botocore.exceptions import ClientError
from settings import Settings

settings = Settings()

# Создание клиента S3 с указанием учетных данных и настроек
s3_client = boto3.client(
    "s3",
    endpoint_url=settings.s3_endpoint_url,
    aws_access_key_id=settings.s3_access_key,
    aws_secret_access_key=settings.s3_secret_key
)

def upload_file(file, bucket_name, key):
    s3_client.upload_fileobj(file, bucket_name, key)

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