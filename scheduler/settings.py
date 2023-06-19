from pydantic import BaseSettings

class Settings(BaseSettings):
    db_username: str
    db_password: str
    db_host: str
    db_port: str
    db_name: str
    kafka_bootstrap_servers: str
    s3_bucket_name: str
    s3_access_key: str
    s3_secret_key: str
    s3_endpoint_url: str

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
