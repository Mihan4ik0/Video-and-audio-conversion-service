from kafka import KafkaConsumer
from pydantic import BaseModel
from settings import Settings

class ConversionTask(BaseModel):
    file_id: str
    target_format: str

# Загрузка настроек
settings = Settings()

# Создание Kafka-потребителя
consumer = KafkaConsumer("conversion_tasks", bootstrap_servers=settings.kafka_bootstrap_servers)

for message in consumer:
    task = ConversionTask.parse_raw(message.value)
    # Здесь код для выполнения задачи конвертации,
    # обновления статуса задачи и сохранения результатов в базе данных
