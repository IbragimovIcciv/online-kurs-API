import pytest
from fastapi import status

def test_register_user(client):
    """Тест регистрации нового пользователя"""
    response = client.post(
        "/auth/register",
        json={
            "full_name": "New User",
            "email": "newuser@example.com",
            "password": "newpassword123"
        }
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["email"] == "newuser@example.com"
    assert data["full_name"] == "New User"
    assert data["is_active"] == True
    assert data["is_admin"] == False
    assert "id" in data


def test_register_existing_email(client, test_user):
    """Тест регистрации с уже существующим email"""
    response = client.post(
        "/auth/register",
        json={
            "full_name": "Another User",
            "email": "testuser@example.com",  # Уже существующий email
            "password": "password123"
        }
    )
    
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Email уже зарегистрирован" in response.json()["detail"]


def test_login_correct_credentials(client, test_user):
    """Тест входа с правильными учетными данными"""
    response = client.post(
        "/auth/token",
        data={
            "username": "testuser@example.com",
            "password": "testpassword"
        }
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_incorrect_credentials(client):
    """Тест входа с неправильными учетными данными"""
    response = client.post(
        "/auth/token",
        data={
            "username": "wrong@example.com",
            "password": "wrongpassword"
        }
    )
    
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert "Неверный email или пароль" in response.json()["detail"]
