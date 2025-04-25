from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from sqlalchemy import func

from app import models, schemas
from app.database import get_db
from app.security import get_current_user, get_current_admin_user

router = APIRouter(prefix="/lessons", tags=["Lessons"])

@router.post("/", response_model=schemas.LessonResponse)
async def create_lesson(
    lesson_data: schemas.LessonCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Создание нового урока для курса"""
    # Проверка существования курса
    course = db.query(models.Course).filter(models.Course.id == lesson_data.course_id).first()
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Курс не найден"
        )
    
    # Проверка прав доступа (автор курса или администратор)
    if course.author_id != current_user.id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав для добавления уроков к этому курсу"
        )
    
    # Создание нового урока
    new_lesson = models.Lesson(
        course_id=lesson_data.course_id,
        title=lesson_data.title,
        video_url=lesson_data.video_url,
        content=lesson_data.content,
        order=lesson_data.order
    )
    
    db.add(new_lesson)
    db.commit()
    db.refresh(new_lesson)
    
    return new_lesson

@router.get("/", response_model=List[schemas.LessonResponse])
async def get_lessons(
    course_id: int = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Получение списка уроков с возможностью фильтрации по курсу"""
    query = db.query(models.Lesson)
    
    # Применение фильтра по курсу, если он указан
    if course_id:
        query = query.filter(models.Lesson.course_id == course_id)
    
    # Сортировка по порядковому номеру
    query = query.order_by(models.Lesson.order)
    
    lessons = query.offset(skip).limit(limit).all()
    return lessons

@router.get("/{lesson_id}", response_model=schemas.LessonWithCommentsRatings)
async def get_lesson(
    lesson_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Получение информации о конкретном уроке, его комментариях и рейтинге"""
    # Получение урока
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
    
    # Получение среднего рейтинга
    avg_rating = db.query(func.avg(models.Rating.stars)).filter(
        models.Rating.lesson_id == lesson_id
    ).scalar()
    
    # Добавление среднего рейтинга к результату
    lesson_data = schemas.LessonWithCommentsRatings.from_orm(lesson)
    lesson_data.average_rating = round(float(avg_rating), 1) if avg_rating else None
    
    return lesson_data

@router.put("/{lesson_id}", response_model=schemas.LessonResponse)
async def update_lesson(
    lesson_id: int,
    lesson_data: schemas.LessonUpdate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Обновление информации об уроке"""
    # Получение урока
    lesson = db.query(models.Lesson).filter(models.Lesson.id == lesson_id).first()
    if not lesson:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Урок не найден"
        )
    
    # Получение связанного курса
    course = db.query(models.Course).filter(models.Course.id == lesson.course_id).first()
    
    # Проверка прав доступа (автор курса или администратор)
    if course.author_id != current_user.id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав для изменения этого урока"
        )
    
    # Обновление данных
    if lesson_data.title:
        lesson.title = lesson_data.title
    if lesson_data.video_url:
        lesson.video_url = lesson_data.video_url
    if lesson_data.content:
        lesson.content = lesson_data.content
    if lesson_data.order is not None:
        lesson.order = lesson_data.order
    
    db.commit()
    db.refresh(lesson)
    
    return lesson

@router.delete("/{lesson_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_lesson(
    lesson_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Удаление урока"""
    # Получение урока
    lesson = db.query(models.Lesson).filter(models.Lesson.id == lesson_id).first()
    if not lesson:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Урок не найден"
        )
    
    # Получение связанного курса
    course = db.query(models.Course).filter(models.Course.id == lesson.course_id).first()
    
    # Проверка прав доступа (автор курса или администратор)
    if course.author_id != current_user.id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав для удаления этого урока"
        )
    
    db.delete(lesson)
    db.commit()
    
    return None
