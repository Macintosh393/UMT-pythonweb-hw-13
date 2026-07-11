import pytest
from unittest.mock import MagicMock
from src.database.models import User, Role
from src.database.db import get_db
from src.services.auth import create_email_token

async def get_auth_header_and_user(client, db_session, username, email, is_admin=False):
    # Register
    await client.post(
        "/api/auth/register",
        json={"username": username, "email": email, "password": "password123"}
    )
    # Confirm email
    token = await create_email_token({"sub": email})
    await client.get(f"/api/auth/confirm_email/{token}")
    
    # If admin required, modify user role in DB
    if is_admin:
        from sqlalchemy import select
        stmt = select(User).filter_by(username=username)
        res = await db_session.execute(stmt)
        user = res.scalar_one()
        user.role = Role.ADMIN
        await db_session.commit()

    # Login
    login_res = await client.post(
        "/api/auth/login",
        data={"username": username, "password": "password123"}
    )
    access_token = login_res.json()["access_token"]
    return {"Authorization": f"Bearer {access_token}"}

@pytest.mark.asyncio
async def test_get_me(client, db_session):
    headers = await get_auth_header_and_user(client, db_session, "meuser", "meuser@example.com")
    
    response = await client.get("/api/users/me", headers=headers)
    assert response.status_code == 200
    assert response.json()["username"] == "meuser"

@pytest.mark.asyncio
async def test_update_avatar_forbidden_for_user(client, db_session):
    headers = await get_auth_header_and_user(client, db_session, "stduser", "stduser@example.com", is_admin=False)
    
    # Try uploading avatar
    files = {"file": ("avatar.png", b"fake image bytes", "image/png")}
    response = await client.patch("/api/users/avatar", files=files, headers=headers)
    assert response.status_code == 403
    assert response.json()["detail"] == "Operation forbidden: Admin role required"

@pytest.mark.asyncio
async def test_update_avatar_allowed_for_admin(client, db_session, monkeypatch):
    # Mock Cloudinary UploadFileService
    upload_mock = MagicMock(return_value="http://cloudinary.url/avatar.png")
    monkeypatch.setattr("src.services.upload_file.UploadFileService.upload_file", upload_mock)

    headers = await get_auth_header_and_user(client, db_session, "adminuser", "adminuser@example.com", is_admin=True)
    
    # Upload avatar as admin
    files = {"file": ("avatar.png", b"fake image bytes", "image/png")}
    response = await client.patch("/api/users/avatar", files=files, headers=headers)
    assert response.status_code == 200
    assert response.json()["avatar_url"] == "http://cloudinary.url/avatar.png"
    upload_mock.assert_called_once()
