import boto3
from botocore.exceptions import ClientError
from settings import Settings
import os

settings = Settings()

# Создание клиента S3 с указанием учетных данных и настроек
s3_client = boto3.client(
    "s3",
    endpoint_url=settings.s3_endpoint_url,
    aws_access_key_id=settings.s3_access_key,
    aws_secret_access_key=settings.s3_secret_key
)

def upload_file(file, bucket_name, key):
    try:
        s3_client.upload_fileobj(file, bucket_name, key)
    except ClientError as e:
        raise Exception(f"Failed to upload file: {str(e)}")

def delete_file(bucket_name, directory_path):
    # Получение списка объектов в указанном каталоге
    objects_to_delete = []
    paginator = s3_client.get_paginator('list_objects_v2')
    page_iterator = paginator.paginate(Bucket=bucket_name, Prefix=directory_path)
    for page in page_iterator:
        if 'Contents' in page:
            for obj in page['Contents']:
                objects_to_delete.append({'Key': obj['Key']})
    
    # Удаление объектов
    if len(objects_to_delete) > 0:
        try:
            s3_client.delete_objects(Bucket=bucket_name, Delete={'Objects': objects_to_delete})
        except ClientError as e:
            raise Exception(f"Failed to delete objects: {str(e)}")
    else:
        raise Exception("No objects found in the specified directory.")

def check_file_exists(bucket_name, key):
    try:
        s3_client.head_object(Bucket=bucket_name, Key=key)
        return True
    except ClientError:
        return False

def download_file(bucket_name, key, file_path):
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'wb') as f:
            s3_client.download_fileobj(bucket_name, key, f)
    except Exception as e:
        raise Exception("Failed to download file:", str(e))
