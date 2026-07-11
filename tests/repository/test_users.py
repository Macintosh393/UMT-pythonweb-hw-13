import pytest
from src.repository.users import UserRepository
from src.schemas.users import UserCreate
from src.database.models import User, Role

@pytest.mark.asyncio
async def test_create_user(db_session):
    repo = UserRepository(db_session)
    user_data = UserCreate(
        username="testuser",
        email="testuser@example.com",
        password="hashedpassword123",
    )
    user = await repo.create_user(user_data)
    assert user.id is not None
    assert user.username == "testuser"
    assert user.email == "testuser@example.com"
    assert user.hashed_password == "hashedpassword123"
    assert user.role == Role.USER

@pytest.mark.asyncio
async def test_get_user_by_id(db_session):
    repo = UserRepository(db_session)
    user_data = UserCreate(
        username="testuser",
        email="testuser@example.com",
        password="hashedpassword123",
    )
    created_user = await repo.create_user(user_data)
    
    fetched_user = await repo.get_user_by_id(created_user.id)
    assert fetched_user is not None
    assert fetched_user.username == "testuser"

@pytest.mark.asyncio
async def test_get_user_by_username(db_session):
    repo = UserRepository(db_session)
    user_data = UserCreate(
        username="testuser",
        email="testuser@example.com",
        password="hashedpassword123",
    )
    await repo.create_user(user_data)
    
    fetched_user = await repo.get_user_by_username("testuser")
    assert fetched_user is not None
    assert fetched_user.username == "testuser"

@pytest.mark.asyncio
async def test_get_user_by_email(db_session):
    repo = UserRepository(db_session)
    user_data = UserCreate(
        username="testuser",
        email="testuser@example.com",
        password="hashedpassword123",
    )
    await repo.create_user(user_data)
    
    fetched_user = await repo.get_user_by_email("testuser@example.com")
    assert fetched_user is not None
    assert fetched_user.email == "testuser@example.com"

@pytest.mark.asyncio
async def test_confirm_email(db_session):
    repo = UserRepository(db_session)
    user_data = UserCreate(
        username="testuser",
        email="testuser@example.com",
        password="hashedpassword123",
    )
    user = await repo.create_user(user_data)
    assert user.confirmed is False
    
    await repo.confirm_email("testuser@example.com")
    assert user.confirmed is True

@pytest.mark.asyncio
async def test_update_avatar_url(db_session):
    repo = UserRepository(db_session)
    user_data = UserCreate(
        username="testuser",
        email="testuser@example.com",
        password="hashedpassword123",
    )
    user = await repo.create_user(user_data)
    
    updated_user = await repo.update_avatar_url("testuser@example.com", "http://avatar.url")
    assert updated_user.avatar_url == "http://avatar.url"

@pytest.mark.asyncio
async def test_update_password(db_session):
    repo = UserRepository(db_session)
    user_data = UserCreate(
        username="testuser",
        email="testuser@example.com",
        password="hashedpassword123",
    )
    user = await repo.create_user(user_data)
    
    await repo.update_password("testuser@example.com", "newhashedpassword")
    assert user.hashed_password == "newhashedpassword"
