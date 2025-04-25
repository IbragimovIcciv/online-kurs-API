import pytest
from fastapi import status

def test_create_lesson(authorized_client, test_course):
    """Тест создания нового урока"""
    response = authorized_client.post(
        "/lessons/",
        json={
            "course_id": test_course.id,
            "title": "New Lesson",
            "video_url": "https://example.com/video1.mp4",
            "content": "This is the content of the new lesson",
            "order": 1
        }
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["title"] == "New Lesson"
    assert data["video_url"] == "https://example.com/video1.mp4"
    assert data["content"] == "This is the content of the new lesson"
    assert data["course_id"] == test_course.id
    assert data["order"] == 1
    assert "id" in data


def test_create_lesson_not_author(authorized_client, db, test_admin):
    """Тест создания урока не автором курса"""
    # Создадим курс от имени администратора
    from app.models import Course
    admin_course = Course(
        title="Admin Course",
        description="This is admin's course",
        author_id=test_admin.id
    )
    db.add(admin_course)
    db.commit()
    
    # Пытаемся добавить урок обычным пользователем
    response = authorized_client.post(
        "/lessons/",
        json={
            "course_id": admin_course.id,
            "title": "Unauthorized Lesson",
            "video_url": "https://example.com/video.mp4",
            "content": "This shouldn't work",
            "order": 1
        }
    )
    
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert "Недостаточно прав" in response.json()["detail"]


def test_get_lessons(client, test_lesson):
    """Тест получения списка всех уроков"""
    response = client.get("/lessons/")
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert any(lesson["id"] == test_lesson.id for lesson in data)


def test_get_lessons_by_course(client, test_lesson):
    """Тест получения уроков конкретного курса"""
    response = client.get(f"/lessons/?course_id={test_lesson.course_id}")
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert all(lesson["course_id"] == test_lesson.course_id for lesson in data)


def test_get_specific_lesson(authorized_client, test_lesson, db):
    """Тест получения информации о конкретном уроке"""
    # Создаем запись о записи на курс для тестового пользователя
    from app.models import Enrollment
    enrollment = Enrollment(
        user_id=2,  # test_user.id (обычно 2 в тестовой базе)
        course_id=test_lesson.course_id
    )
    db.add(enrollment)
    db.commit()
    
    response = authorized_client.get(f"/lessons/{test_lesson.id}")
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == test_lesson.id
    assert data["title"] == test_lesson.title
    assert data["video_url"] == test_lesson.video_url
    assert data["content"] == test_lesson.content
    assert "comments" in data
    assert "average_rating" in data


def test_get_lesson_not_enrolled(authorized_client, test_lesson):
    """Тест получения урока пользователем, не записанным на курс"""
    # Предполагается, что пользователь не записан на курс
    response = authorized_client.get(f"/lessons/{test_lesson.id}")
    
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert "Вы не записаны на этот курс" in response.json()["detail"]


def test_update_lesson(authorized_client, test_lesson):
    """Тест обновления информации об уроке"""
    # Сначала запишем пользователя на курс
    from app.models import Enrollment
    enrollment_response = authorized_client.post(f"/courses/enroll/{test_lesson.course_id}")
    assert enrollment_response.status_code == status.HTTP_200_OK
    
    # Теперь обновим урок
    response = authorized_client.put(
        f"/lessons/{test_lesson.id}",
        json={
            "title": "Updated Lesson",
            "video_url": "https://example.com/updated.mp4",
            "content": "This is an updated lesson content",
            "order": 2
        }
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["title"] == "Updated Lesson"
    assert data["video_url"] == "https://example.com/updated.mp4"
    assert data["content"] == "This is an updated lesson content"
    assert data["order"] == 2


def test_delete_lesson(authorized_client, test_lesson, db):
    """Тест удаления урока"""
    # Сначала запишем пользователя на курс
    from app.models import Enrollment
    enrollment_response = authorized_client.post(f"/courses/enroll/{test_lesson.course_id}")
    assert enrollment_response.status_code == status.HTTP_200_OK
    
    # Теперь удалим урок
    response = authorized_client.delete(f"/lessons/{test_lesson.id}")
    
    assert response.status_code == status.HTTP_204_NO_CONTENT
    
    # Проверка, что урок действительно удален из базы данных
    from app.models import Lesson
    deleted_lesson = db.query(Lesson).filter(Lesson.id == test_lesson.id).first()
    assert deleted_lesson is None
