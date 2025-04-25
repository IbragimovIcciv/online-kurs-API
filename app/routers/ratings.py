from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from sqlalchemy import func

from app import models, schemas
from app.database import get_db
from app.security import get_current_user, get_current_admin_user

router = APIRouter(prefix="/ratings", tags=["Ratings"])

@router.post("/", response_model=schemas.RatingResponse)
async def create_or_update_rating(
    rating_data: schemas.RatingCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Создание или обновление оценки для урока"""
    # Проверка существования урока
    lesson = db.query(models.Lesson).filter(models.Lesson.id == rating_data.lesson_id).first()
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
    
    if not enrollment:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Вы не записаны на этот курс"
        )
    
    # Проверка, существует ли уже оценка от этого пользователя
    existing_rating = db.query(models.Rating).filter(
        models.Rating.user_id == current_user.id,
        models.Rating.lesson_id == rating_data.lesson_id
    ).first()
    
    if existing_rating:
        # Обновление существующей оценки
        existing_rating.stars = rating_data.stars
        db.commit()
        db.refresh(existing_rating)
        return existing_rating
    else:
        # Создание новой оценки
        new_rating = models.Rating(
            user_id=current_user.id,
            lesson_id=rating_data.lesson_id,
            stars=rating_data.stars
        )
        
        db.add(new_rating)
        db.commit()
        db.refresh(new_rating)
        
        return new_rating

@router.get("/lesson/{lesson_id}", response_model=List[schemas.RatingResponse])
async def get_lesson_ratings(
    lesson_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Получение всех оценок для урока"""
    # Проверка существования урока
    lesson = db.query(models.Lesson).filter(models.Lesson.id == lesson_id).first()
    if not lesson:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Урок не найден"
        )
    
    # Проверка, записан ли пользователь на курс или является ли автором/админом
    course = db.query(models.Course).filter(models.Course.id == lesson.course_id).first()
    enrollment = db.query(models.Enrollment).filter(
        models.Enrollment.user_id == current_user.id,
        models.Enrollment.course_id == lesson.course_id
    ).first()
    
    if not enrollment and course.author_id != current_user.id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Вы не записаны на этот курс"
        )
    
    # Получение всех оценок
    ratings = db.query(models.Rating).filter(
        models.Rating.lesson_id == lesson_id
    ).offset(skip).limit(limit).all()
    
    return ratings

@router.get("/lesson/{lesson_id}/average", response_model=float)
async def get_lesson_average_rating(
    lesson_id: int,
    db: Session = Depends(get_db)
):
    """Получение средней оценки урока"""
    # Проверка существования урока
    lesson = db.query(models.Lesson).filter(models.Lesson.id == lesson_id).first()
    if not lesson:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Урок не найден"
        )
    
    # Вычисление среднего рейтинга
    avg_rating = db.query(func.avg(models.Rating.stars)).filter(
        models.Rating.lesson_id == lesson_id
    ).scalar()
    
    if avg_rating is None:
        return 0.0
    
    return round(float(avg_rating), 1)

@router.get("/my", response_model=List[schemas.RatingResponse])
async def get_my_ratings(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Получение всех оценок текущего пользователя"""
    ratings = db.query(models.Rating).filter(
        models.Rating.user_id == current_user.id
    ).offset(skip).limit(limit).all()
    
    return ratings

@router.delete("/{rating_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_rating(
    rating_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Удаление оценки"""
    # Проверка существования оценки
    rating = db.query(models.Rating).filter(models.Rating.id == rating_id).first()
    if not rating:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Оценка не найдена"
        )
    
    # Проверка прав доступа (автор оценки или администратор)
    if rating.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав для удаления этой оценки"
        )
    
    db.delete(rating)
    db.commit()
    
    return None
