import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.security import get_current_user, get_current_admin_user
from app import models
from main import app

# Создание тестовой базы данных в памяти
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db():
    # Создание таблиц в тестовой базе данных
    Base.metadata.create_all(bind=engine)
    
    # Использование тестовой сессии для тестов
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        # Очистка после каждого теста
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db):
    # Переопределение зависимости для использования тестовой БД
    def override_get_db():
        try:
            yield db
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as client:
        yield client
    
    # Сброс переопределений после тестов
    app.dependency_overrides = {}


@pytest.fixture(scope="function")
def test_user(db):
    # Создание тестового пользователя
    from app.security import get_password_hash
    
    user = models.User(
        full_name="Test User",
        email="testuser@example.com",
        hashed_password=get_password_hash("testpassword"),
        is_active=True,
        is_admin=False
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    return user


@pytest.fixture(scope="function")
def test_admin(db):
    # Создание тестового администратора
    from app.security import get_password_hash
    
    admin = models.User(
        full_name="Test Admin",
        email="testadmin@example.com",
        hashed_password=get_password_hash("testpassword"),
        is_active=True,
        is_admin=True
    )
    db.add(admin)
    db.commit()
    db.refresh(admin)
    
    return admin


@pytest.fixture(scope="function")
def token_headers(client, test_user):
    # Получение токена для тестового пользователя
    response = client.post(
        "/auth/token",
        data={"username": test_user.email, "password": "testpassword"}
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="function")
def admin_token_headers(client, test_admin):
    # Получение токена для тестового администратора
    response = client.post(
        "/auth/token",
        data={"username": test_admin.email, "password": "testpassword"}
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="function")
def authorized_client(client, token_headers):
    # Клиент с авторизационным токеном обычного пользователя
    client.headers.update(token_headers)
    return client


@pytest.fixture(scope="function")
def admin_client(client, admin_token_headers):
    # Клиент с авторизационным токеном администратора
    client.headers.update(admin_token_headers)
    return client


@pytest.fixture(scope="function")
def test_course(db, test_user):
    # Создание тестового курса
    course = models.Course(
        title="Test Course",
        description="This is a test course",
        author_id=test_user.id
    )
    db.add(course)
    db.commit()
    db.refresh(course)
    
    return course


@pytest.fixture(scope="function")
def test_lesson(db, test_course):
    # Создание тестового урока
    lesson = models.Lesson(
        course_id=test_course.id,
        title="Test Lesson",
        video_url="https://example.com/video.mp4",
        content="This is the content of the test lesson",
        order=1
    )
    db.add(lesson)
    db.commit()
    db.refresh(lesson)
    
    return lesson
