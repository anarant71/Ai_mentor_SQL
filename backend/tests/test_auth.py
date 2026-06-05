"""Tests for the auth endpoints."""

from app.services.auth import ACCESS_COOKIE


def test_register_user_success(client):
    """Test successful user registration."""
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "test@example.com",
            "password": "password123",
            "display_name": "Test User"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "test@example.com"
    assert data["display_name"] == "Test User"
    assert "id" in data
    cookies = dict(response.cookies)
    assert ACCESS_COOKIE in cookies


def test_register_user_invalid_email(client):
    """Test registration with invalid email."""
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "invalid-email",
            "password": "password123",
            "display_name": "Test User"
        }
    )
    assert response.status_code == 422


def test_register_user_short_password(client):
    """Test registration with short password."""
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "test@example.com",
            "password": "123",
            "display_name": "Test User"
        }
    )
    assert response.status_code == 422


def test_register_user_missing_name(client):
    """Test registration with missing name."""
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "test@example.com",
            "password": "password123",
            "display_name": ""
        }
    )
    assert response.status_code == 422


def test_register_duplicate_email(client):
    """Test registration with duplicate email."""
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "duplicate@example.com",
            "password": "password123",
            "display_name": "Test User"
        }
    )
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "duplicate@example.com",
            "password": "password123",
            "display_name": "Test User 2"
        }
    )
    assert response.status_code == 409


def test_login_success(client):
    """Test successful login."""
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "login@example.com",
            "password": "password123",
            "display_name": "Login User"
        }
    )
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "login@example.com",
            "password": "password123"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "login@example.com"
    assert data["display_name"] == "Login User"
    cookies = dict(response.cookies)
    assert ACCESS_COOKIE in cookies


def test_login_invalid_credentials(client):
    """Test login with invalid credentials."""
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "nonexistent@example.com",
            "password": "wrongpassword"
        }
    )
    assert response.status_code == 401


def test_get_current_user(client):
    """Test getting current user info via cookie."""
    register_response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "current@example.com",
            "password": "password123",
            "display_name": "Current User"
        }
    )
    assert register_response.status_code == 201

    response = client.get("/api/v1/auth/me")
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "current@example.com"
    assert data["display_name"] == "Current User"
