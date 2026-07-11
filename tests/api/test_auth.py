import pytest
from unittest.mock import AsyncMock
from src.services.auth import create_email_token, create_reset_token, Hash
from src.database.models import User

@pytest.mark.asyncio
async def test_register_user(client, mock_fastmail):
    response = await client.post(
        "/api/auth/register",
        json={
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "strongpassword123",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["username"] == "newuser"
    assert data["email"] == "newuser@example.com"
    mock_fastmail.assert_called_once()

@pytest.mark.asyncio
async def test_register_duplicate_username(client):
    # First registration
    await client.post(
        "/api/auth/register",
        json={
            "username": "dupuser",
            "email": "dup1@example.com",
            "password": "password123",
        },
    )
    # Duplicate username registration
    response = await client.post(
        "/api/auth/register",
        json={
            "username": "dupuser",
            "email": "dup2@example.com",
            "password": "password123",
        },
    )
    assert response.status_code == 409
    assert response.json()["detail"] == "The username is already taken. Try another one"

@pytest.mark.asyncio
async def test_confirm_email(client):
    # Register and manually confirm
    await client.post(
        "/api/auth/register",
        json={
            "username": "confirmuser",
            "email": "confirmuser@example.com",
            "password": "password123",
        },
    )
    
    token = await create_email_token({"sub": "confirmuser@example.com"})
    response = await client.get(f"/api/auth/confirm_email/{token}")
    assert response.status_code == 200
    assert response.json()["message"] == "Your email has been successfully confirmed!"

@pytest.mark.asyncio
async def test_login_user(client):
    # Register and confirm
    await client.post(
        "/api/auth/register",
        json={
            "username": "loginuser",
            "email": "loginuser@example.com",
            "password": "password123",
        },
    )
    token = await create_email_token({"sub": "loginuser@example.com"})
    await client.get(f"/api/auth/confirm_email/{token}")

    # Login
    response = await client.post(
        "/api/auth/login",
        data={
            "username": "loginuser",
            "password": "password123",
        },
    )
    assert response.status_code == 200
    assert "access_token" in response.json()

@pytest.mark.asyncio
async def test_request_password_reset(client, mock_fastmail):
    # Register
    await client.post(
        "/api/auth/register",
        json={
            "username": "resetuser",
            "email": "resetuser@example.com",
            "password": "password123",
        },
    )
    
    mock_fastmail.reset_mock()
    response = await client.post(
        "/api/auth/request-password-reset",
        json={"email": "resetuser@example.com"},
    )
    assert response.status_code == 200
    mock_fastmail.assert_called_once()

@pytest.mark.asyncio
async def test_reset_password(client):
    # Register
    await client.post(
        "/api/auth/register",
        json={
            "username": "resetexecuser",
            "email": "resetexecuser@example.com",
            "password": "password123",
        },
    )

    token = await create_reset_token({"sub": "resetexecuser@example.com"})
    response = await client.post(
        f"/api/auth/reset-password/{token}",
        json={"new_password": "newpassword456"},
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Your password has been successfully reset!"

    # Verify we can login with the new password
    token_confirm = await create_email_token({"sub": "resetexecuser@example.com"})
    await client.get(f"/api/auth/confirm_email/{token_confirm}")
    
    login_response = await client.post(
        "/api/auth/login",
        data={
            "username": "resetexecuser",
            "password": "newpassword456",
        },
    )
    assert login_response.status_code == 200
