from kafka import KafkaProducer
from pydantic import BaseModel

class ConversionTask(BaseModel):
    file_id: str
    target_format: str

# Создание Kafka-производителя
producer = KafkaProducer(bootstrap_servers="localhost:9092")

def send_conversion_task(task: ConversionTask):
    producer.send("conversion_tasks", task.json().encode())