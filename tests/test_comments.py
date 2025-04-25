import pytest
from fastapi import status

def test_create_comment(authorized_client, test_lesson, test_user, db):
    """Тест создания нового комментария"""
    # Сначала запишем пользователя на курс
    from app.models import Enrollment
    enrollment = Enrollment(
        user_id=test_user.id,
        course_id=test_lesson.course_id
    )
    db.add(enrollment)
    db.commit()
    
    response = authorized_client.post(
        "/comments/",
        json={
            "lesson_id": test_lesson.id,
            "text": "This is a test comment"
        }
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["text"] == "This is a test comment"
    assert data["user_id"] == test_user.id
    assert data["lesson_id"] == test_lesson.id
    assert "id" in data
    assert "created_at" in data


def test_create_comment_not_enrolled(authorized_client, test_lesson):
    """Тест создания комментария пользователем, не записанным на курс"""
    response = authorized_client.post(
        "/comments/",
        json={
            "lesson_id": test_lesson.id,
            "text": "This comment should not be created"
        }
    )
    
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert "Вы не записаны на этот курс" in response.json()["detail"]


def test_get_lesson_comments(authorized_client, test_lesson, test_user, db):
    """Тест получения комментариев к уроку"""
    # Запись на курс
    from app.models import Enrollment
    enrollment = Enrollment(
        user_id=test_user.id,
        course_id=test_lesson.course_id
    )
    db.add(enrollment)
    
    # Создание тестового комментария
    from app.models import Comment
    comment = Comment(
        user_id=test_user.id,
        lesson_id=test_lesson.id,
        text="Test comment for getting comments"
    )
    db.add(comment)
    db.commit()
    
    # Получение комментариев
    response = authorized_client.get(f"/comments/lesson/{test_lesson.id}")
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert any(c["text"] == "Test comment for getting comments" for c in data)


def test_update_comment(authorized_client, test_lesson, test_user, db):
    """Тест обновления комментария"""
    # Запись на курс
    from app.models import Enrollment
    enrollment = Enrollment(
        user_id=test_user.id,
        course_id=test_lesson.course_id
    )
    db.add(enrollment)
    
    # Создание тестового комментария
    from app.models import Comment
    comment = Comment(
        user_id=test_user.id,
        lesson_id=test_lesson.id,
        text="Original comment text"
    )
    db.add(comment)
    db.commit()
    
    # Обновление комментария
    response = authorized_client.put(
        f"/comments/{comment.id}",
        json={
            "text": "Updated comment text"
        }
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["text"] == "Updated comment text"
    assert data["id"] == comment.id


def test_update_comment_not_author(authorized_client, test_lesson, test_user, db, test_admin):
    """Тест обновления чужого комментария"""
    # Запись на курс
    from app.models import Enrollment
    enrollment = Enrollment(
        user_id=test_user.id,
        course_id=test_lesson.course_id
    )
    db.add(enrollment)
    
    # Создание комментария от имени администратора
    from app.models import Comment
    admin_comment = Comment(
        user_id=test_admin.id,
        lesson_id=test_lesson.id,
        text="Admin's comment text"
    )
    db.add(admin_comment)
    db.commit()
    
    # Попытка обновления комментария обычным пользователем
    response = authorized_client.put(
        f"/comments/{admin_comment.id}",
        json={
            "text": "Trying to modify admin's comment"
        }
    )
    
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert "Недостаточно прав" in response.json()["detail"]


def test_delete_comment(authorized_client, test_lesson, test_user, db):
    """Тест удаления комментария"""
    # Запись на курс
    from app.models import Enrollment
    enrollment = Enrollment(
        user_id=test_user.id,
        course_id=test_lesson.course_id
    )
    db.add(enrollment)
    
    # Создание тестового комментария
    from app.models import Comment
    comment = Comment(
        user_id=test_user.id,
        lesson_id=test_lesson.id,
        text="Comment that will be deleted"
    )
    db.add(comment)
    db.commit()
    
    # Удаление комментария
    response = authorized_client.delete(f"/comments/{comment.id}")
    
    assert response.status_code == status.HTTP_204_NO_CONTENT
    
    # Проверка, что комментарий действительно удален
    deleted_comment = db.query(Comment).filter(Comment.id == comment.id).first()
    assert deleted_comment is None
