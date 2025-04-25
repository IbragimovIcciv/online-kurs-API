from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from sqlalchemy import func, desc

from app import models, schemas
from app.database import get_db
from app.security import get_current_admin_user

router = APIRouter(tags=["Admin"])

@router.get("/stats/courses", response_model=List[schemas.CourseStats])
async def get_course_stats(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_admin_user)
):
    """Получение статистики по курсам (только для администраторов)"""
    # Подзапрос для подсчета количества студентов на каждом курсе
    courses_with_students = db.query(
        models.Course.id,
        models.Course.title,
        func.count(models.Enrollment.id).label("total_students")
    ).outerjoin(
        models.Enrollment, models.Course.id == models.Enrollment.course_id
    ).group_by(
        models.Course.id
    ).subquery()
    
    # Подзапрос для подсчета количества уроков на каждом курсе
    courses_with_lessons = db.query(
        models.Course.id,
        func.count(models.Lesson.id).label("total_lessons")
    ).outerjoin(
        models.Lesson, models.Course.id == models.Lesson.course_id
    ).group_by(
        models.Course.id
    ).subquery()
    
    # Подзапрос для вычисления среднего рейтинга курса
    courses_with_ratings = db.query(
        models.Lesson.course_id,
        func.avg(models.Rating.stars).label("average_rating")
    ).join(
        models.Rating, models.Lesson.id == models.Rating.lesson_id
    ).group_by(
        models.Lesson.course_id
    ).subquery()
    
    # Объединение всех подзапросов
    results = db.query(
        courses_with_students.c.id.label("course_id"),
        courses_with_students.c.title,
        courses_with_students.c.total_students,
        courses_with_lessons.c.total_lessons,
        courses_with_ratings.c.average_rating
    ).outerjoin(
        courses_with_lessons, courses_with_students.c.id == courses_with_lessons.c.id
    ).outerjoin(
        courses_with_ratings, courses_with_students.c.id == courses_with_ratings.c.course_id
    ).offset(skip).limit(limit).all()
    
    # Преобразование результатов в список схем CourseStats
    stats = []
    for result in results:
        stats.append(schemas.CourseStats(
            course_id=result.course_id,
            title=result.title,
            total_students=result.total_students or 0,
            total_lessons=result.total_lessons or 0,
            average_rating=round(float(result.average_rating), 1) if result.average_rating else None
        ))
    
    return stats

@router.get("/stats/users", response_model=List[schemas.UserStats])
async def get_user_stats(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_admin_user)
):
    """Получение статистики по пользователям (только для администраторов)"""
    # Подзапрос для подсчета количества курсов, на которые записан каждый пользователь
    users_with_courses = db.query(
        models.User.id,
        models.User.full_name,
        func.count(models.Enrollment.id).label("total_courses_enrolled")
    ).outerjoin(
        models.Enrollment, models.User.id == models.Enrollment.user_id
    ).group_by(
        models.User.id
    ).subquery()
    
    # Подзапрос для подсчета количества комментариев каждого пользователя
    users_with_comments = db.query(
        models.User.id,
        func.count(models.Comment.id).label("total_comments")
    ).outerjoin(
        models.Comment, models.User.id == models.Comment.user_id
    ).group_by(
        models.User.id
    ).subquery()
    
    # Подзапрос для подсчета количества оценок каждого пользователя
    users_with_ratings = db.query(
        models.User.id,
        func.count(models.Rating.id).label("total_ratings")
    ).outerjoin(
        models.Rating, models.User.id == models.Rating.user_id
    ).group_by(
        models.User.id
    ).subquery()
    
    # Объединение всех подзапросов
    results = db.query(
        users_with_courses.c.id.label("user_id"),
        users_with_courses.c.full_name,
        users_with_courses.c.total_courses_enrolled,
        users_with_comments.c.total_comments,
        users_with_ratings.c.total_ratings
    ).outerjoin(
        users_with_comments, users_with_courses.c.id == users_with_comments.c.id
    ).outerjoin(
        users_with_ratings, users_with_courses.c.id == users_with_ratings.c.id
    ).offset(skip).limit(limit).all()
    
    # Преобразование результатов в список схем UserStats
    stats = []
    for result in results:
        stats.append(schemas.UserStats(
            user_id=result.user_id,
            full_name=result.full_name,
            total_courses_enrolled=result.total_courses_enrolled or 0,
            total_comments=result.total_comments or 0,
            total_ratings=result.total_ratings or 0
        ))
    
    return stats

@router.get("/stats/popular-lessons", response_model=List[schemas.LessonResponse])
async def get_popular_lessons(
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_admin_user)
):
    """Получение самых популярных уроков на основе рейтинга (только для администраторов)"""
    # Подзапрос для вычисления среднего рейтинга каждого урока
    lessons_with_ratings = db.query(
        models.Lesson.id,
        func.avg(models.Rating.stars).label("average_rating"),
        func.count(models.Rating.id).label("rating_count")
    ).outerjoin(
        models.Rating, models.Lesson.id == models.Rating.lesson_id
    ).group_by(
        models.Lesson.id
    ).having(
        func.count(models.Rating.id) > 0  # Только уроки с оценками
    ).subquery()
    
    # Получение уроков с высоким рейтингом
    popular_lesson_ids = db.query(
        lessons_with_ratings.c.id
    ).order_by(
        desc(lessons_with_ratings.c.average_rating),
        desc(lessons_with_ratings.c.rating_count)
    ).limit(limit).all()
    
    popular_lesson_ids = [id for (id,) in popular_lesson_ids]
    
    if not popular_lesson_ids:
        return []
    
    # Получение полной информации о популярных уроках
    popular_lessons = db.query(models.Lesson).filter(
        models.Lesson.id.in_(popular_lesson_ids)
    ).all()
    
    return popular_lessons

@router.get("/stats/active-users", response_model=List[schemas.UserResponse])
async def get_active_users(
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_admin_user)
):
    """Получение самых активных пользователей (только для администраторов)"""
    # Подзапрос для подсчета активности пользователей (комментарии + оценки)
    users_activity = db.query(
        models.User.id,
        (
            func.count(models.Comment.id) + 
            func.count(models.Rating.id)
        ).label("activity_count")
    ).outerjoin(
        models.Comment, models.User.id == models.Comment.user_id
    ).outerjoin(
        models.Rating, models.User.id == models.Rating.user_id
    ).group_by(
        models.User.id
    ).subquery()
    
    # Получение ID самых активных пользователей
    active_user_ids = db.query(
        users_activity.c.id
    ).order_by(
        desc(users_activity.c.activity_count)
    ).limit(limit).all()
    
    active_user_ids = [id for (id,) in active_user_ids]
    
    if not active_user_ids:
        return []
    
    # Получение полной информации о самых активных пользователях
    active_users = db.query(models.User).filter(
        models.User.id.in_(active_user_ids)
    ).all()
    
    return active_users
