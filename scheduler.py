import uuid
from fastapi import FastAPI, UploadFile, File as FastAPIFile, Form
from pydantic import BaseModel
from kafka import KafkaProducer
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import File as FileModel, Task
from s3 import upload_file, download_file, check_file_exists
import json
from fastapi.encoders import jsonable_encoder
from fastapi.responses import FileResponse

app = FastAPI()

class ConversionTask(BaseModel):
    file_id: str
    target_format: str

# Создание Kafka-производителя
producer = KafkaProducer(bootstrap_servers="localhost:9092")

# Создание соединения с базой данных
engine = create_engine('sqlite:///convertationbd.db')
Session = sessionmaker(bind=engine)
session = Session()

@app.post("/convert")
async def convert_file(file: UploadFile = FastAPIFile(...), target_format: str = Form(...)):
    # Генерация айди файла
    file_id = str(uuid.uuid4())

    if file:
        # Сохранение файла на S3
        bucket_name = "my-bucket"
        key = f"{file_id}/{file.filename}"
        with open(file.filename, "wb") as f:
            contents = await file.read()
            f.write(contents)
        upload_file(file.filename, bucket_name, key)
    else:
        # Загрузка файла с S3
        bucket_name = "my-bucket"
        key = "<S3 key of the existing file>"
        file_path = f"/tmp/{file_id}"
        download_file(bucket_name, key, file_path)

    # Сохранение информации о файле и задаче в базе данных
    file = FileModel(filename=file.filename, file_type=target_format)
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
    file = session.query(FileModel).filter_by(id=file_id).first()
    if not file:
        return {"message": "File not found"}

    # Получение информации о задании из базы данных
    task = session.query(Task).filter_by(file_id=file_id).first()
    if not task:
        return {"message": "Task not found"}

    # Если задание не завершено, возвращаем уведомление
    if task.status != "Complete":
        return {"message": "Task is not complete. Current status: " + task.status}

    # Загрузка файла с S3
    bucket_name = "my-bucket"
    key = f"{file_id}/{file.filename}"
    file_path = f"/tmp/{file_id}"
    
    # Проверка существования файла
    if not check_file_exists(bucket_name, key):
        return {"message": "File does not exist"}

    try:
        download_file(bucket_name, key, file_path)
    except Exception as e:
        return {"message": f"Failed to download file: {str(e)}"}

    # Возврат файла как ответа
    return FileResponse(file_path, filename=file.filename)



if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
