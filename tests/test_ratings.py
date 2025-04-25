import pytest
from fastapi import status

def test_create_rating(authorized_client, test_lesson, test_user, db):
    """Тест создания новой оценки"""
    # Сначала запишем пользователя на курс
    from app.models import Enrollment
    enrollment = Enrollment(
        user_id=test_user.id,
        course_id=test_lesson.course_id
    )
    db.add(enrollment)
    db.commit()
    
    response = authorized_client.post(
        "/ratings/",
        json={
            "lesson_id": test_lesson.id,
            "stars": 5
        }
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["stars"] == 5
    assert data["user_id"] == test_user.id
    assert data["lesson_id"] == test_lesson.id
    assert "id" in data


def test_create_rating_not_enrolled(authorized_client, test_lesson):
    """Тест создания оценки пользователем, не записанным на курс"""
    response = authorized_client.post(
        "/ratings/",
        json={
            "lesson_id": test_lesson.id,
            "stars": 3
        }
    )
    
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert "Вы не записаны на этот курс" in response.json()["detail"]


def test_create_rating_invalid_stars(authorized_client, test_lesson, test_user, db):
    """Тест создания оценки с недопустимым количеством звезд"""
    # Запись на курс
    from app.models import Enrollment
    enrollment = Enrollment(
        user_id=test_user.id,
        course_id=test_lesson.course_id
    )
    db.add(enrollment)
    db.commit()
    
    # Попытка создать оценку с 6 звездами (максимум 5)
    response = authorized_client.post(
        "/ratings/",
        json={
            "lesson_id": test_lesson.id,
            "stars": 6
        }
    )
    
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert "Stars must be between 1 and 5" in response.json()["detail"][0]["msg"]


def test_update_existing_rating(authorized_client, test_lesson, test_user, db):
    """Тест обновления существующей оценки"""
    # Запись на курс
    from app.models import Enrollment
    enrollment = Enrollment(
        user_id=test_user.id,
        course_id=test_lesson.course_id
    )
    db.add(enrollment)
    
    # Создание тестовой оценки
    from app.models import Rating
    rating = Rating(
        user_id=test_user.id,
        lesson_id=test_lesson.id,
        stars=2
    )
    db.add(rating)
    db.commit()
    
    # Обновление оценки
    response = authorized_client.post(
        "/ratings/",
        json={
            "lesson_id": test_lesson.id,
            "stars": 4
        }
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["stars"] == 4
    
    # Проверка, что в базе данных только одна оценка от этого пользователя для этого урока
    ratings_count = db.query(Rating).filter(
        Rating.user_id == test_user.id,
        Rating.lesson_id == test_lesson.id
    ).count()
    assert ratings_count == 1


def test_get_lesson_ratings(authorized_client, test_lesson, test_user, db):
    """Тест получения оценок урока"""
    # Запись на курс
    from app.models import Enrollment
    enrollment = Enrollment(
        user_id=test_user.id,
        course_id=test_lesson.course_id
    )
    db.add(enrollment)
    
    # Создание тестовой оценки
    from app.models import Rating
    rating = Rating(
        user_id=test_user.id,
        lesson_id=test_lesson.id,
        stars=5
    )
    db.add(rating)
    db.commit()
    
    # Получение оценок
    response = authorized_client.get(f"/ratings/lesson/{test_lesson.id}")
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert any(r["stars"] == 5 for r in data)


def test_get_lesson_average_rating(client, test_lesson, test_user, db):
    """Тест получения средней оценки урока"""
    # Создание нескольких оценок от разных пользователей
    from app.models import Rating, User
    from app.security import get_password_hash
    
    # Создаем дополнительных пользователей
    user1 = User(
        full_name="Rating User 1",
        email="ratinguser1@example.com",
        hashed_password=get_password_hash("password"),
        is_active=True
    )
    user2 = User(
        full_name="Rating User 2",
        email="ratinguser2@example.com",
        hashed_password=get_password_hash("password"),
        is_active=True
    )
    db.add_all([user1, user2])
    db.commit()
    
    # Создаем оценки (5 + 3 + 4) / 3 = 4.0
    rating1 = Rating(user_id=test_user.id, lesson_id=test_lesson.id, stars=5)
    rating2 = Rating(user_id=user1.id, lesson_id=test_lesson.id, stars=3)
    rating3 = Rating(user_id=user2.id, lesson_id=test_lesson.id, stars=4)
    db.add_all([rating1, rating2, rating3])
    db.commit()
    
    # Получение средней оценки
    response = client.get(f"/ratings/lesson/{test_lesson.id}/average")
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data == 4.0  # Средняя оценка должна быть 4.0


def test_get_my_ratings(authorized_client, test_lesson, test_user, db):
    """Тест получения всех оценок текущего пользователя"""
    # Создание двух тестовых уроков
    from app.models import Lesson, Rating
    lesson2 = Lesson(
        course_id=test_lesson.course_id,
        title="Another Test Lesson",
        video_url="https://example.com/video2.mp4",
        content="Content of another test lesson",
        order=2
    )
    db.add(lesson2)
    db.commit()
    
    # Запись на курс
    from app.models import Enrollment
    enrollment = Enrollment(
        user_id=test_user.id,
        course_id=test_lesson.course_id
    )
    db.add(enrollment)
    
    # Создание оценок для обоих уроков
    rating1 = Rating(user_id=test_user.id, lesson_id=test_lesson.id, stars=4)
    rating2 = Rating(user_id=test_user.id, lesson_id=lesson2.id, stars=5)
    db.add_all([rating1, rating2])
    db.commit()
    
    # Получение оценок пользователя
    response = authorized_client.get("/ratings/my")
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 2
    assert any(r["lesson_id"] == test_lesson.id and r["stars"] == 4 for r in data)
    assert any(r["lesson_id"] == lesson2.id and r["stars"] == 5 for r in data)


def test_delete_rating(authorized_client, test_lesson, test_user, db):
    """Тест удаления оценки"""
    # Запись на курс
    from app.models import Enrollment
    enrollment = Enrollment(
        user_id=test_user.id,
        course_id=test_lesson.course_id
    )
    db.add(enrollment)
    
    # Создание тестовой оценки
    from app.models import Rating
    rating = Rating(
        user_id=test_user.id,
        lesson_id=test_lesson.id,
        stars=3
    )
    db.add(rating)
    db.commit()
    
    # Удаление оценки
    response = authorized_client.delete(f"/ratings/{rating.id}")
    
    assert response.status_code == status.HTTP_204_NO_CONTENT
    
    # Проверка, что оценка действительно удалена
    deleted_rating = db.query(Rating).filter(Rating.id == rating.id).first()
    assert deleted_rating is None
