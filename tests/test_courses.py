import pytest
from fastapi import status

def test_create_course(authorized_client, test_user):
    """Тест создания нового курса"""
    response = authorized_client.post(
        "/courses/",
        json={
            "title": "New Course",
            "description": "This is a new test course"
        }
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["title"] == "New Course"
    assert data["description"] == "This is a new test course"
    assert data["author_id"] == test_user.id
    assert "id" in data
    assert "created_at" in data


def test_get_courses(client, test_course):
    """Тест получения списка всех курсов"""
    response = client.get("/courses/")
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert any(course["id"] == test_course.id for course in data)


def test_get_courses_with_search(client, test_course, db):
    """Тест поиска курсов"""
    # Создадим дополнительный курс с другим названием
    from app.models import Course
    other_course = Course(
        title="Python Programming",
        description="Learn Python programming",
        author_id=test_course.author_id
    )
    db.add(other_course)
    db.commit()
    
    # Поиск по слову "Python"
    response = client.get("/courses/?search=Python")
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["title"] == "Python Programming"


def test_get_specific_course(client, test_course):
    """Тест получения информации о конкретном курсе"""
    response = client.get(f"/courses/{test_course.id}")
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == test_course.id
    assert data["title"] == test_course.title
    assert data["description"] == test_course.description
    assert "lessons" in data  # Должен содержать список уроков


def test_update_course(authorized_client, test_course):
    """Тест обновления информации о курсе"""
    response = authorized_client.put(
        f"/courses/{test_course.id}",
        json={
            "title": "Updated Course",
            "description": "This is an updated course description"
        }
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["title"] == "Updated Course"
    assert data["description"] == "This is an updated course description"


def test_update_course_not_author(authorized_client, db, test_admin):
    """Тест обновления курса не автором"""
    # Создадим курс от имени администратора
    from app.models import Course
    admin_course = Course(
        title="Admin Course",
        description="This is admin's course",
        author_id=test_admin.id
    )
    db.add(admin_course)
    db.commit()
    
    # Пытаемся обновить курс обычным пользователем
    response = authorized_client.put(
        f"/courses/{admin_course.id}",
        json={
            "title": "Hacked Course",
            "description": "Trying to hack the course"
        }
    )
    
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert "Недостаточно прав" in response.json()["detail"]


def test_delete_course(authorized_client, test_course, db):
    """Тест удаления курса"""
    response = authorized_client.delete(f"/courses/{test_course.id}")
    
    assert response.status_code == status.HTTP_204_NO_CONTENT
    
    # Проверка, что курс действительно удален из базы данных
    from app.models import Course
    deleted_course = db.query(Course).filter(Course.id == test_course.id).first()
    assert deleted_course is None


def test_enroll_in_course(authorized_client, test_user, db):
    """Тест записи на курс"""
    # Создадим курс от имени другого пользователя
    from app.models import Course, User
    
    # Создаем другого пользователя
    from app.security import get_password_hash
    other_user = User(
        full_name="Other User",
        email="otheruser@example.com",
        hashed_password=get_password_hash("password"),
        is_active=True
    )
    db.add(other_user)
    db.commit()
    
    # Создаем курс от имени другого пользователя
    other_course = Course(
        title="Other Course",
        description="Course by other user",
        author_id=other_user.id
    )
    db.add(other_course)
    db.commit()
    
    # Записываемся на курс
    response = authorized_client.post(f"/courses/enroll/{other_course.id}")
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["user_id"] == test_user.id
    assert data["course_id"] == other_course.id


def test_get_enrolled_courses(authorized_client, test_user, test_course, db):
    """Тест получения списка курсов, на которые записан пользователь"""
    # Создаем запись о регистрации на курс
    from app.models import Enrollment
    enrollment = Enrollment(
        user_id=test_user.id,
        course_id=test_course.id
    )
    db.add(enrollment)
    db.commit()
    
    # Получаем список курсов
    response = authorized_client.get("/courses/enrolled/my")
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["id"] == test_course.id
