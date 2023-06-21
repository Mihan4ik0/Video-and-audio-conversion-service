import uuid
import os
import json
from fastapi import FastAPI, UploadFile, File as FastAPIFile, Form, HTTPException
from pydantic import BaseModel, ValidationError, validator
from kafka import KafkaProducer
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import File as FileModel, Task
from s3 import upload_file, download_file, check_file_exists, delete_file
from fastapi.responses import FileResponse
from settings import Settings
from datetime import datetime, timedelta
import time
from broker import send_conversion_task


app = FastAPI()

# Загрузка настроек
settings = Settings()

class ConversionTask(BaseModel):
    file_id: str
    target_format: str

    @validator('file_id')
    def validate_file_id(cls, file_id):
        # Дополнительная логика проверки file_id, если требуется
        return file_id

    @validator('target_format')
    def validate_target_format(cls, target_format):
        allowed_formats = [
            # Аудио форматы
            'mp3',
            'wav',
            'flac',
            'aac',
            'ogg',
            'wma',
            'alac',
            'm4a',
            'ape',

            # Видео форматы
            'mp4',
            'avi',
            'mov',
            'wmv',
            'flv',
            'mpeg',
            '3gp',
            'webm',
            'vob'
        ]

        if target_format not in allowed_formats:
            raise ValueError(f"Invalid target format. Allowed formats: {', '.join(allowed_formats)}")
        return target_format

# Создание соединения с базой данных
db_url = f"postgresql://{settings.db_username}:{settings.db_password}@{settings.db_host}:{settings.db_port}/{settings.db_name}"
engine = create_engine(db_url)
Session = sessionmaker(bind=engine)
session = Session()

@app.post("/convert")
async def convert_file(file: UploadFile = FastAPIFile(...), target_format: str = Form(...)):
    # Генерация айди файлаtime
    file_id = str(uuid.uuid4())

    # Получение базового имени файла без расширения
    filename_base, file_extension = os.path.splitext(file.filename)

    # Сохранение файла на S3
    bucket_name = settings.s3_bucket_name
    key = f"{file_id}/{file.filename}"
    upload_file(file.file, bucket_name, key)

    # Сохранение информации о файле и задаче в базе данных
    file_model = FileModel(filename=filename_base, initial_file_type=file_extension, file_type=target_format, s3_id=file_id)
    session.add(file_model)
    session.commit()

    task = Task(file_id=file_model.id, status="Scheduled")
    session.add(task)
    session.commit()

    # Отправка задачи в Kafka
    send_conversion_task(file_id.encode())

    return {"file_id": file_id, "message": "Task scheduled"}




@app.get("/files/{file_id}")
async def get_file(file_id: str):
    # Получение информации о файле из базы данных
    file_model = session.query(FileModel).filter_by(s3_id=file_id).first()
    if not file_model:
        error_message = "File not found"
        raise HTTPException(status_code=404, detail=error_message)

    # Получение информации о задании из базы данных
    task = session.query(Task).filter_by(file_id=file_model.id).first()
    if not task:
        error_message = "Task not found"
        raise HTTPException(status_code=404, detail=error_message)

    # Если задание не завершено, возвращаем уведомление
    if task.status != "Complete":
        error_message = f"Task is not complete. Current status: {task.status}"
        raise HTTPException(status_code=400, detail=error_message)

    # Получение конечного типа файла из базы данных
    file_type = session.query(FileModel.file_type).filter_by(s3_id=file_id).scalar()

    # Загрузка файла с S3
    bucket_name = settings.s3_bucket_name
    key = f"{file_id}/{file_model.filename}.{file_model.file_type}"
    file_path = f"/tmp/{file_id}"

    # Проверка существования файла
    if not check_file_exists(bucket_name, key):
        error_message = f"File {key} in bucket {bucket_name} does not exist"
        raise HTTPException(status_code=404, detail=error_message)

    try:
        download_file(bucket_name, key, file_path)
    except Exception as e:
        error_message = f"Failed to download file: {str(e)}"
        raise HTTPException(status_code=500, detail=error_message)

    # Возврат файла как ответа с правильным типом контента
    return FileResponse(file_path, filename=file_model.filename, media_type=file_type)

def check_files():
    # Определяем текущее время
    current_time = datetime.now()

    # Вычисляем время, прошедшее более часа назад
    hour_ago = current_time - timedelta(hours=1)

    # Получаем файлы, у которых прошло более часа с момента выполнения
    files = session.query(FileModel).join(Task).filter(Task.completed_at < hour_ago).all()

    # Выводим s3_id этих файлов
    for file in files:
        bucket_name = settings.s3_bucket_name
        key = f"{file.s3_id}"

        # Проверяем на существование и удаление
        if check_file_exists(bucket_name, key):
            delete_file(bucket_name, key)

    # Закрываем сессию
    session.close()

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
    while True:
        check_files(desired_hours=settings.desired_hours)
        time.sleep(3600) 
