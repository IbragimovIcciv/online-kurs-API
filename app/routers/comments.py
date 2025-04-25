from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app import models, schemas
from app.database import get_db
from app.security import get_current_user, get_current_admin_user

router = APIRouter(prefix="/comments", tags=["Comments"])

@router.post("/", response_model=schemas.CommentResponse)
async def create_comment(
    comment_data: schemas.CommentCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Создание нового комментария к уроку"""
    # Проверка существования урока
    lesson = db.query(models.Lesson).filter(models.Lesson.id == comment_data.lesson_id).first()
    if not lesson:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Урок не найден"
        )
    
    # Проверка, записан ли пользователь на курс
    enrollment = db.query(models.Enrollment).filter(
        models.Enrollment.user_id == current_user.id,
        models.Enrollment.course_id == lesson.course_id
    ).first()
    
    # Если пользователь не записан на курс и не является автором или администратором
    course = db.query(models.Course).filter(models.Course.id == lesson.course_id).first()
    if not enrollment and course.author_id != current_user.id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Вы не записаны на этот курс"
        )
    
    # Создание комментария
    new_comment = models.Comment(
        user_id=current_user.id,
        lesson_id=comment_data.lesson_id,
        text=comment_data.text
    )
    
    db.add(new_comment)
    db.commit()
    db.refresh(new_comment)
    
    return new_comment

@router.get("/lesson/{lesson_id}", response_model=List[schemas.CommentResponse])
async def get_lesson_comments(
    lesson_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Получение комментариев к конкретному уроку"""
    # Проверка существования урока
    lesson = db.query(models.Lesson).filter(models.Lesson.id == lesson_id).first()
    if not lesson:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Урок не найден"
        )
    
    # Проверка, записан ли пользователь на курс
    enrollment = db.query(models.Enrollment).filter(
        models.Enrollment.user_id == current_user.id,
        models.Enrollment.course_id == lesson.course_id
    ).first()
    
    # Если пользователь не записан на курс и не является автором или администратором
    course = db.query(models.Course).filter(models.Course.id == lesson.course_id).first()
    if not enrollment and course.author_id != current_user.id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Вы не записаны на этот курс"
        )
    
    # Получение комментариев
    comments = db.query(models.Comment).filter(
        models.Comment.lesson_id == lesson_id
    ).order_by(models.Comment.created_at.desc()).offset(skip).limit(limit).all()
    
    return comments

@router.get("/{comment_id}", response_model=schemas.CommentResponse)
async def get_comment(
    comment_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Получение конкретного комментария"""
    # Получение комментария
    comment = db.query(models.Comment).filter(models.Comment.id == comment_id).first()
    if not comment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Комментарий не найден"
        )
    
    # Получение связанного урока и курса
    lesson = db.query(models.Lesson).filter(models.Lesson.id == comment.lesson_id).first()
    course = db.query(models.Course).filter(models.Course.id == lesson.course_id).first()
    
    # Проверка, записан ли пользователь на курс
    enrollment = db.query(models.Enrollment).filter(
        models.Enrollment.user_id == current_user.id,
        models.Enrollment.course_id == course.id
    ).first()
    
    # Если пользователь не записан на курс и не является автором или администратором
    if not enrollment and course.author_id != current_user.id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Вы не записаны на этот курс"
        )
    
    return comment

@router.put("/{comment_id}", response_model=schemas.CommentResponse)
async def update_comment(
    comment_id: int,
    comment_data: schemas.CommentBase,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Обновление комментария"""
    # Получение комментария
    comment = db.query(models.Comment).filter(models.Comment.id == comment_id).first()
    if not comment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Комментарий не найден"
        )
    
    # Проверка прав доступа (автор комментария или администратор)
    if comment.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав для изменения этого комментария"
        )
    
    # Обновление комментария
    comment.text = comment_data.text
    
    db.commit()
    db.refresh(comment)
    
    return comment

@router.delete("/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_comment(
    comment_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Удаление комментария"""
    # Получение комментария
    comment = db.query(models.Comment).filter(models.Comment.id == comment_id).first()
    if not comment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Комментарий не найден"
        )
    
    # Проверка прав доступа (автор комментария, автор курса или администратор)
    lesson = db.query(models.Lesson).filter(models.Lesson.id == comment.lesson_id).first()
    course = db.query(models.Course).filter(models.Course.id == lesson.course_id).first()
    
    if comment.user_id != current_user.id and course.author_id != current_user.id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав для удаления этого комментария"
        )
    
    db.delete(comment)
    db.commit()
    
    return None
