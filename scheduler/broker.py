from kafka import KafkaProducer
from pydantic import BaseModel
from settings import Settings

class ConversionTaskBroker(BaseModel):
    file_id: str

# Загрузка настроек
settings = Settings()

# Создание Kafka-производителя
producer = KafkaProducer(bootstrap_servers=settings.kafka_bootstrap_servers)

def send_conversion_task(file_id: str):
    task = ConversionTaskBroker(file_id=file_id)
    partition = get_next_partition(total_partitions=settings.total_partitions)
    producer.send("conversion_tasks", task.json().encode(), partition=partition)

def get_next_partition(total_partitions):
    current_partition = getattr(get_next_partition, "current_partition", 0)
    next_partition = (current_partition + 1) % total_partitions
    setattr(get_next_partition, "current_partition", next_partition)
    return next_partition
