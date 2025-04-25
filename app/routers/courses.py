from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from sqlalchemy import func

from app import models, schemas
from app.database import get_db
from app.security import get_current_user, get_current_admin_user

router = APIRouter(prefix="/courses", tags=["Courses"])

@router.post("/", response_model=schemas.CourseResponse)
async def create_course(
    course_data: schemas.CourseCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Создание нового курса"""
    new_course = models.Course(
        title=course_data.title,
        description=course_data.description,
        author_id=current_user.id
    )
    
    db.add(new_course)
    db.commit()
    db.refresh(new_course)
    
    return new_course

@router.get("/", response_model=List[schemas.CourseResponse])
async def get_courses(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Получение списка всех курсов с возможностью поиска"""
    query = db.query(models.Course)
    
    # Применение фильтра поиска, если он указан
    if search:
        query = query.filter(
            models.Course.title.ilike(f"%{search}%") | 
            models.Course.description.ilike(f"%{search}%")
        )
    
    courses = query.offset(skip).limit(limit).all()
    return courses

@router.get("/{course_id}", response_model=schemas.CourseWithLessons)
async def get_course(
    course_id: int,
    db: Session = Depends(get_db)
):
    """Получение информации о конкретном курсе и его уроках"""
    course = db.query(models.Course).filter(models.Course.id == course_id).first()
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Курс не найден"
        )
    
    return course

@router.put("/{course_id}", response_model=schemas.CourseResponse)
async def update_course(
    course_id: int,
    course_data: schemas.CourseUpdate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Обновление информации о курсе"""
    course = db.query(models.Course).filter(models.Course.id == course_id).first()
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Курс не найден"
        )
    
    # Проверка прав доступа (автор курса или администратор)
    if course.author_id != current_user.id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав для изменения этого курса"
        )
    
    # Обновление данных
    if course_data.title:
        course.title = course_data.title
    if course_data.description:
        course.description = course_data.description
    
    db.commit()
    db.refresh(course)
    
    return course

@router.delete("/{course_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_course(
    course_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Удаление курса"""
    course = db.query(models.Course).filter(models.Course.id == course_id).first()
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Курс не найден"
        )
    
    # Проверка прав доступа (автор курса или администратор)
    if course.author_id != current_user.id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав для удаления этого курса"
        )
    
    db.delete(course)
    db.commit()
    
    return None

@router.post("/enroll/{course_id}", response_model=schemas.EnrollmentResponse)
async def enroll_in_course(
    course_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Запись пользователя на курс"""
    # Проверка существования курса
    course = db.query(models.Course).filter(models.Course.id == course_id).first()
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Курс не найден"
        )
    
    # Проверка, не записан ли пользователь уже на этот курс
    existing_enrollment = db.query(models.Enrollment).filter(
        models.Enrollment.user_id == current_user.id,
        models.Enrollment.course_id == course_id
    ).first()
    
    if existing_enrollment:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Вы уже записаны на этот курс"
        )
    
    # Создание новой записи
    enrollment = models.Enrollment(
        user_id=current_user.id,
        course_id=course_id
    )
    
    db.add(enrollment)
    db.commit()
    db.refresh(enrollment)
    
    return enrollment

@router.get("/enrolled/my", response_model=List[schemas.CourseResponse])
async def get_enrolled_courses(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Получение списка курсов, на которые записан текущий пользователь"""
    enrollments = db.query(models.Enrollment).filter(
        models.Enrollment.user_id == current_user.id
    ).all()
    
    course_ids = [enrollment.course_id for enrollment in enrollments]
    
    if not course_ids:
        return []
    
    courses = db.query(models.Course).filter(
        models.Course.id.in_(course_ids)
    ).all()
    
    return courses

@router.get("/{course_id}/students", response_model=List[schemas.UserResponse])
async def get_course_students(
    course_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Получение списка студентов, записанных на курс (только для автора курса или администратора)"""
    # Проверка существования курса
    course = db.query(models.Course).filter(models.Course.id == course_id).first()
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Курс не найден"
        )
    
    # Проверка прав доступа
    if course.author_id != current_user.id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав для просмотра списка студентов"
        )
    
    # Получение пользователей, записанных на курс
    enrollments = db.query(models.Enrollment).filter(
        models.Enrollment.course_id == course_id
    ).all()
    
    user_ids = [enrollment.user_id for enrollment in enrollments]
    
    if not user_ids:
        return []
    
    users = db.query(models.User).filter(
        models.User.id.in_(user_ids)
    ).all()
    
    return users
