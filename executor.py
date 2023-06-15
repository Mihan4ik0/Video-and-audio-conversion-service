from kafka import KafkaConsumer
from pydantic import BaseModel

class ConversionTask(BaseModel):
    file_id: str
    target_format: str

# Создание Kafka-потребителя
consumer = KafkaConsumer("conversion_tasks", bootstrap_servers="localhost:9092")

for message in consumer:
    task = ConversionTask.parse_raw(message.value)
    # Здесь код для выполнения задачи конвертации,
    # обновления статуса задачи и сохранения результатов в базе данных