import uuid
from fastapi import FastAPI, UploadFile, File as FastAPIFile, Form, HTTPException
from pydantic import BaseModel
from kafka import KafkaProducer
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import File as FileModel, Task
from s3 import upload_file, download_file, check_file_exists
import json
from fastapi.encoders import jsonable_encoder
from fastapi.responses import FileResponse, Response
from settings import Settings

app = FastAPI()

# Загрузка настроек
settings = Settings()

class ConversionTask(BaseModel):
    file_id: str
    target_format: str

# Создание Kafka-производителя
producer = KafkaProducer(bootstrap_servers=settings.kafka_bootstrap_servers)

# Создание соединения с базой данных
db_url = f"postgresql://{settings.db_username}:{settings.db_password}@{settings.db_host}:{settings.db_port}/{settings.db_name}"
engine = create_engine(db_url)
Session = sessionmaker(bind=engine)
session = Session()

@app.post("/convert")
async def convert_file(file: UploadFile = FastAPIFile(...), target_format: str = Form(...)):
    # Генерация айди файла
    file_id = str(uuid.uuid4())

    # Сохранение файла на S3
    bucket_name = settings.s3_bucket_name
    key = f"{file_id}/{file.filename}"
    upload_file(file.file, bucket_name, key)

    # Сохранение информации о файле и задаче в базе данных
    file = FileModel(filename=file.filename, file_type=target_format, s3_id=file_id)
    session.add(file)
    session.commit()

    task = Task(file_id=file.id, status="Scheduled")
    session.add(task)
    session.commit()

    # Отправка задачи в Kafka
    task_data = jsonable_encoder(task)
    producer.send("conversion_tasks", json.dumps(task_data).encode())

    return {"file_id": file_id, "message": "Task scheduled"}



@app.get("/file/{file_id}")
async def get_file(file_id: str):
    # Получение информации о файле из базы данных
    file = session.query(FileModel).filter_by(s3_id=file_id).first()
    if not file:
        error_message = "File not found"
        raise HTTPException(status_code=404, detail=error_message)

    # Получение информации о задании из базы данных
    task = session.query(Task).filter_by(file_id=file.id).first()
    if not task:
        error_message = "Task not found"
        raise HTTPException(status_code=404, detail=error_message)

    # Если задание не завершено, возвращаем уведомление
    if task.status != "Complete":
        error_message = f"Task is not complete. Current status: {task.status}"
        raise HTTPException(status_code=400, detail=error_message)

    # Загрузка файла с S3
    bucket_name = settings.s3_bucket_name
    key = f"{file_id}/{file.filename}"
    file_path = f"/tmp/{file_id}"
    
    # Проверка существования файла
    if not check_file_exists(bucket_name, key):
        error_message = "File does not exist"
        raise HTTPException(status_code=404, detail=error_message)

    try:
        download_file(bucket_name, key, file_path)
    except Exception as e:
        error_message = f"Failed to download file: {str(e)}"
        raise HTTPException(status_code=500, detail=error_message)

    # Возврат файла как ответа
    return FileResponse(file_path, filename=file.filename)



if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
