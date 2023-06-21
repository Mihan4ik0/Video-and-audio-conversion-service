import os
import json
from kafka import KafkaConsumer, TopicPartition
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker
from models import Task, File
from s3 import download_file, upload_file, delete_file
from settings import Settings
import ffmpeg
import base64

# Загрузка настроек
settings = Settings()

# Создание соединения с базой данных
db_url = f"postgresql://{settings.db_username}:{settings.db_password}@{settings.db_host}:{settings.db_port}/{settings.db_name}"
engine = create_engine(db_url)
Session = sessionmaker(bind=engine)
session = Session()

def convert_file(input_path, output_path, target_format):
    # Используйте ffmpeg для конвертации файла
    try:
        input_stream = ffmpeg.input(input_path)
        output_stream = ffmpeg.output(input_stream, output_path, format=target_format)
        ffmpeg.run(output_stream)
        return True
    except ffmpeg.Error as e:
        raise Exception(f"Error converting file: {e.stderr}")

def conversion_worker(partition_number):
    consumer = KafkaConsumer(
        bootstrap_servers=settings.kafka_bootstrap_servers,
        group_id="conversion_group"
    )
    topic_partition = TopicPartition("conversion_tasks", partition_number)
    consumer.assign([topic_partition])

    for message in consumer:
        try:
            file_id = message.value.decode("utf-8")
            data = json.loads(file_id)
            file_id = data["file_id"]
        except UnicodeDecodeError as e:
            raise Exception(f"Error decoding file_id: {e}")
        
        # Загрузка файла с S3
        bucket_name = settings.s3_bucket_name
        file = session.query(File).filter_by(s3_id=file_id).first()
        if not file:
            raise Exception(f"File not found for task")
        file_id = file_id.strip()
        input_path = f"/tmp/{file_id}/{file.filename}{file.initial_file_type}"
        key = f"{file_id}/{file.filename}{file.initial_file_type}"
        download_file(bucket_name, key, input_path)
        delete_file(bucket_name, key)
        task = session.query(Task).filter(Task.file_id == file.id).first()

        # Обработка задачи конвертации
        if task.status == "Scheduled":  
            task.status = "In process"
            session.commit()

            # Выполнение конвертации
            output_path = f"/tmp/{file_id}/{file.filename}.{file.file_type}"
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            success = convert_file(input_path, output_path, file.file_type)

            if success:
                # Загрузка обработанного файла в S3
                with open(output_path, "rb") as f:
                    key = f"{file_id}/{file.filename}.{file.file_type}"
                    upload_file(f, bucket_name, key)

                # Удаление локальных копий файлов
                os.remove(input_path)
                os.remove(output_path)

                # Обновление статуса задачи и времени завершения в базе данных
                task.status = "Complete"
                task.completed_at = func.now()
                session.commit()
            else:
                # Конвертация не удалась, обновление статуса задачи
                task.status = "Retry conversion"
                session.commit()

if __name__ == "__main__":
    partition_number = int(os.environ.get("PARTITION_NUMBER", "0"))
    conversion_worker(partition_number)
