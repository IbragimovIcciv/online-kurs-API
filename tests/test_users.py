import pytest
from fastapi import status

def test_get_current_user(authorized_client, test_user):
    """Тест получения информации о текущем пользователе"""
    response = authorized_client.get("/users/me")
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["email"] == test_user.email
    assert data["full_name"] == test_user.full_name
    assert data["id"] == test_user.id


def test_get_current_user_unauthorized(client):
    """Тест получения информации о текущем пользователе без авторизации"""
    response = client.get("/users/me")
    
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert "Could not validate credentials" in response.json()["detail"]


def test_update_current_user(authorized_client, test_user, db):
    """Тест обновления данных текущего пользователя"""
    response = authorized_client.put(
        "/users/me",
        json={
            "full_name": "Updated Name",
            "email": "updated@example.com"
        }
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["full_name"] == "Updated Name"
    assert data["email"] == "updated@example.com"
    
    # Проверка, что изменения сохранились в базе данных
    updated_user = db.query(pytest.importorskip("app.models").User).filter_by(id=test_user.id).first()
    assert updated_user.full_name == "Updated Name"
    assert updated_user.email == "updated@example.com"


def test_get_all_users_admin(admin_client):
    """Тест получения списка всех пользователей администратором"""
    response = admin_client.get("/users/")
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1  # Должен быть как минимум один пользователь


def test_get_all_users_not_admin(authorized_client):
    """Тест получения списка всех пользователей не администратором"""
    response = authorized_client.get("/users/")
    
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert "Not enough permissions" in response.json()["detail"]


def test_get_specific_user_admin(admin_client, test_user):
    """Тест получения информации о конкретном пользователе администратором"""
    response = admin_client.get(f"/users/{test_user.id}")
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == test_user.id
    assert data["email"] == test_user.email
    assert data["full_name"] == test_user.full_name


def test_update_user_admin(admin_client, test_user, db):
    """Тест обновления данных пользователя администратором"""
    response = admin_client.put(
        f"/users/{test_user.id}",
        json={
            "full_name": "Admin Updated Name",
            "email": "adminupdated@example.com"
        }
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["full_name"] == "Admin Updated Name"
    assert data["email"] == "adminupdated@example.com"
    
    # Проверка, что изменения сохранились в базе данных
    updated_user = db.query(pytest.importorskip("app.models").User).filter_by(id=test_user.id).first()
    assert updated_user.full_name == "Admin Updated Name"
    assert updated_user.email == "adminupdated@example.com"
