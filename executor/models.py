from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.orm import declarative_base
from sqlalchemy.sql import func
from sqlalchemy.orm import sessionmaker
from settings import Settings

settings = Settings()

database_url = f"postgresql://{settings.db_username}:{settings.db_password}@{settings.db_host}:{settings.db_port}/{settings.db_name}"
engine = create_engine(database_url)
Session = sessionmaker(bind=engine)
session = Session()

Base = declarative_base()

# Команда для удаления таблицы, если она уже существует
Base.metadata.drop_all(bind=engine)

class File(Base):
    __tablename__ = 'files'

    id = Column(Integer, primary_key=True)
    filename = Column(String)
    file_type = Column(String)
    initial_file_type = Column(String)  # Новый столбец для начального типа файла
    s3_id = Column(String)
    created_at = Column(DateTime, default=func.now())

class Task(Base):
    __tablename__ = 'tasks'

    id = Column(Integer, primary_key=True)
    file_id = Column(Integer)
    status = Column(String)
    created_at = Column(DateTime, default=func.now())
    completed_at = Column(DateTime, nullable=True)


Base.metadata.create_all(bind=engine)