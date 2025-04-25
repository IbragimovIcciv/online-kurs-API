from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, validator


# Базовые схемы пользователя
class UserBase(BaseModel):
    full_name: str
    email: EmailStr


class UserCreate(UserBase):
    password: str


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None


class UserResponse(UserBase):
    id: int
    is_active: bool
    is_admin: bool

    class Config:
        orm_mode = True


# Схемы аутентификации
class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    email: Optional[str] = None
    id: Optional[int] = None


# Базовые схемы курса
class CourseBase(BaseModel):
    title: str
    description: str


class CourseCreate(CourseBase):
    pass


class CourseUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None


class CourseResponse(CourseBase):
    id: int
    author_id: int
    created_at: datetime

    class Config:
        orm_mode = True


# Базовые схемы урока
class LessonBase(BaseModel):
    title: str
    video_url: str
    content: str
    order: Optional[int] = 0


class LessonCreate(LessonBase):
    course_id: int


class LessonUpdate(BaseModel):
    title: Optional[str] = None
    video_url: Optional[str] = None
    content: Optional[str] = None
    order: Optional[int] = None


class LessonResponse(LessonBase):
    id: int
    course_id: int

    class Config:
        orm_mode = True


# Схемы для регистрации на курс
class EnrollmentCreate(BaseModel):
    course_id: int


class EnrollmentResponse(BaseModel):
    id: int
    user_id: int
    course_id: int
    enrolled_at: datetime

    class Config:
        orm_mode = True


# Схемы комментариев
class CommentBase(BaseModel):
    text: str


class CommentCreate(CommentBase):
    lesson_id: int


class CommentResponse(CommentBase):
    id: int
    user_id: int
    lesson_id: int
    created_at: datetime

    class Config:
        orm_mode = True


# Схемы оценок
class RatingBase(BaseModel):
    stars: int

    @validator('stars')
    def validate_stars(cls, v):
        if v < 1 or v > 5:
            raise ValueError('Stars must be between 1 and 5')
        return v


class RatingCreate(RatingBase):
    lesson_id: int


class RatingResponse(RatingBase):
    id: int
    user_id: int
    lesson_id: int

    class Config:
        orm_mode = True


# Расширенные схемы для отображения связанных данных
class LessonWithCommentsRatings(LessonResponse):
    comments: List[CommentResponse] = []
    average_rating: Optional[float] = None

    class Config:
        orm_mode = True


class CourseWithLessons(CourseResponse):
    lessons: List[LessonResponse] = []
    author: UserResponse

    class Config:
        orm_mode = True


# Схемы для статистики и админ-панели
class CourseStats(BaseModel):
    course_id: int
    title: str
    total_students: int
    total_lessons: int
    average_rating: Optional[float] = None


class UserStats(BaseModel):
    user_id: int
    full_name: str
    total_courses_enrolled: int
    total_comments: int
    total_ratings: int
