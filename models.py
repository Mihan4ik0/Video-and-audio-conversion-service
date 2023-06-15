from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.orm import declarative_base
from sqlalchemy.sql import func

engine = create_engine('sqlite:///convertationbd.db')
Base = declarative_base()

class File(Base):
    __tablename__ = 'files'

    id = Column(Integer, primary_key=True)
    filename = Column(String)
    file_type = Column(String)
    created_at = Column(DateTime, default=func.now())

class Task(Base):
    __tablename__ = 'tasks'

    id = Column(Integer, primary_key=True)
    file_id = Column(Integer)
    status = Column(String)
    created_at = Column(DateTime, default=func.now())
    completed_at = Column(DateTime, nullable=True)

Base.metadata.create_all(bind=engine)
