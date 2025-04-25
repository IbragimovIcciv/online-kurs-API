import pytest
from fastapi import status

def test_get_course_stats_admin(admin_client, test_course, test_user, db):
    """Тест получения статистики по курсам администратором"""
    # Создание записи на курс
    from app.models import Enrollment, Lesson, Rating
    enrollment = Enrollment(
        user_id=test_user.id,
        course_id=test_course.id
    )
    db.add(enrollment)
    
    # Создание урока
    lesson = Lesson(
        course_id=test_course.id,
        title="Admin Test Lesson",
        video_url="https://example.com/admintest.mp4",
        content="Admin test lesson content",
        order=1
    )
    db.add(lesson)
    db.commit()
    
    # Создание рейтинга
    rating = Rating(
        user_id=test_user.id,
        lesson_id=lesson.id,
        stars=4
    )
    db.add(rating)
    db.commit()
    
    # Получение статистики
    response = admin_client.get("/admin/stats/courses")
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    
    course_stat = next((c for c in data if c["course_id"] == test_course.id), None)
    assert course_stat is not None
    assert course_stat["title"] == test_course.title
    assert course_stat["total_students"] == 1
    assert course_stat["total_lessons"] == 1
    assert course_stat["average_rating"] == 4.0


def test_get_course_stats_not_admin(authorized_client):
    """Тест получения статистики по курсам не администратором"""
    response = authorized_client.get("/admin/stats/courses")
    
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert "Not enough permissions" in response.json()["detail"]


def test_get_user_stats_admin(admin_client, test_user, test_course, db):
    """Тест получения статистики по пользователям администратором"""
    from app.models import Enrollment, Lesson, Comment, Rating
    
    # Создание записи на курс
    enrollment = Enrollment(
        user_id=test_user.id,
        course_id=test_course.id
    )
    db.add(enrollment)
    
    # Создание урока
    lesson = Lesson(
        course_id=test_course.id,
        title="User Stats Test Lesson",
        video_url="https://example.com/userstats.mp4",
        content="User stats test lesson content",
        order=1
    )
    db.add(lesson)
    db.commit()
    
    # Создание комментария
    comment = Comment(
        user_id=test_user.id,
        lesson_id=lesson.id,
        text="User stats test comment"
    )
    db.add(comment)
    
    # Создание рейтинга
    rating = Rating(
        user_id=test_user.id,
        lesson_id=lesson.id,
        stars=5
    )
    db.add(rating)
    db.commit()
    
    # Получение статистики
    response = admin_client.get("/admin/stats/users")
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    
    user_stat = next((u for u in data if u["user_id"] == test_user.id), None)
    assert user_stat is not None
    assert user_stat["full_name"] == test_user.full_name
    assert user_stat["total_courses_enrolled"] == 1
    assert user_stat["total_comments"] == 1
    assert user_stat["total_ratings"] == 1


def test_get_popular_lessons_admin(admin_client, test_lesson, test_user, db):
    """Тест получения популярных уроков администратором"""
    from app.models import Rating
    
    # Создание нескольких рейтингов для урока
    rating1 = Rating(user_id=test_user.id, lesson_id=test_lesson.id, stars=5)
    
    # Создаем еще одного пользователя для дополнительного рейтинга
    from app.models import User
    from app.security import get_password_hash
    another_user = User(
        full_name="Another Rating User",
        email="anotherratinguser@example.com",
        hashed_password=get_password_hash("password"),
        is_active=True
    )
    db.add(another_user)
    db.commit()
    
    rating2 = Rating(user_id=another_user.id, lesson_id=test_lesson.id, stars=4)
    db.add_all([rating1, rating2])
    db.commit()
    
    # Получение популярных уроков
    response = admin_client.get("/admin/stats/popular-lessons")
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    
    # Проверка, что наш урок в списке популярных
    assert any(lesson["id"] == test_lesson.id for lesson in data)


def test_get_active_users_admin(admin_client, test_user, test_lesson, db):
    """Тест получения активных пользователей администратором"""
    from app.models import Comment, Rating
    
    # Создаем активность для тестового пользователя
    comment = Comment(
        user_id=test_user.id,
        lesson_id=test_lesson.id,
        text="Active user test comment"
    )
    rating = Rating(
        user_id=test_user.id,
        lesson_id=test_lesson.id,
        stars=5
    )
    db.add_all([comment, rating])
    db.commit()
    
    # Получение активных пользователей
    response = admin_client.get("/admin/stats/active-users")
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    
    # Проверка, что наш пользователь в списке активных
    assert any(user["id"] == test_user.id for user in data)
