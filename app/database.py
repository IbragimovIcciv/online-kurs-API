from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os

# Загрузка переменных окружения
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./online_courses.db")

# Создание подключения к базе данных
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

# Создание сессии
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Базовый класс для всех моделей
Base = declarative_base()

# Вспомогательная функция для получения сессии базы данных
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
