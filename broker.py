from kafka import KafkaProducer
from pydantic import BaseModel
from settings import Settings

class ConversionTask(BaseModel):
    file_id: str
    target_format: str

# Загрузка настроек
settings = Settings()

# Создание Kafka-производителя
producer = KafkaProducer(bootstrap_servers=settings.kafka_bootstrap_servers)

def send_conversion_task(task: ConversionTask):
    producer.send("conversion_tasks", task.json().encode())
