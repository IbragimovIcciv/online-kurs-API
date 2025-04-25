from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app import models, schemas
from app.database import get_db
from app.security import get_current_user, get_current_admin_user, get_password_hash

router = APIRouter(prefix="/users", tags=["Users"])

@router.get("/me", response_model=schemas.UserResponse)
async def read_current_user(current_user: models.User = Depends(get_current_user)):
    """Получение информации о текущем пользователе"""
    return current_user

@router.put("/me", response_model=schemas.UserResponse)
async def update_current_user(
    user_data: schemas.UserUpdate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Обновление данных текущего пользователя"""
    # Получаем пользователя из базы данных
    db_user = db.query(models.User).filter(models.User.id == current_user.id).first()
    
    # Обновляем данные, если они предоставлены
    if user_data.full_name:
        db_user.full_name = user_data.full_name
    if user_data.email:
        # Проверка на уникальность email
        if db_user.email != user_data.email:
            existing_user = db.query(models.User).filter(models.User.email == user_data.email).first()
            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email уже используется"
                )
        db_user.email = user_data.email
    if user_data.password:
        db_user.hashed_password = get_password_hash(user_data.password)
    
    db.commit()
    db.refresh(db_user)
    
    return db_user

@router.get("/", response_model=List[schemas.UserResponse])
async def get_all_users(
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Получение списка всех пользователей (только для администраторов)"""
    users = db.query(models.User).offset(skip).limit(limit).all()
    return users

@router.get("/{user_id}", response_model=schemas.UserResponse)
async def get_user(
    user_id: int,
    current_user: models.User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Получение информации о конкретном пользователе (только для администраторов)"""
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден"
        )
    return user

@router.put("/{user_id}", response_model=schemas.UserResponse)
async def update_user(
    user_id: int,
    user_data: schemas.UserUpdate,
    current_user: models.User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Обновление данных пользователя администратором"""
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден"
        )
    
    # Обновляем данные, если они предоставлены
    if user_data.full_name:
        db_user.full_name = user_data.full_name
    if user_data.email:
        # Проверка на уникальность email
        if db_user.email != user_data.email:
            existing_user = db.query(models.User).filter(models.User.email == user_data.email).first()
            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email уже используется"
                )
        db_user.email = user_data.email
    if user_data.password:
        db_user.hashed_password = get_password_hash(user_data.password)
    
    db.commit()
    db.refresh(db_user)
    
    return db_user
