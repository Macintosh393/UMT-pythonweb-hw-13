from datetime import datetime, timedelta, UTC
import json
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from jose import JWTError, jwt

from sqlalchemy.ext.asyncio import AsyncSession

from src.database.db import get_db, redis_client
from src.database.models import User, Role
from src.conf.config import config
from src.services.users import UserService


class Hash:
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    def verify_password(self, plain_password, hashed_password):
        return self.pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password: str):
        return self.pwd_context.hash(password)


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


async def create_access_token(data: dict, expires_delta: Optional[int] = None):
    to_encode = data.copy()

    now = datetime.now(UTC)
    if expires_delta:
        expire = now + timedelta(seconds=expires_delta)
    else:
        expire = now + timedelta(seconds=config.JWT_EXPIRATION_SECONDS)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode, config.JWT_SECRET, algorithm=config.JWT_ALGORITHM
    )
    return encoded_jwt


async def get_current_user(
    token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)
):
    credentials_exeption = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Couldn't validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(
            token, config.JWT_SECRET, algorithms=[config.JWT_ALGORITHM]
        )
        username = payload.get("sub")
        if username is None:
            raise credentials_exeption
    except JWTError as e:
        raise credentials_exeption

    cache_key = f"user:{username}"
    try:
        cached_user = await redis_client.get(cache_key)
        if cached_user:
            data = json.loads(cached_user)
            user = User(
                id=data["id"],
                username=data["username"],
                email=data["email"],
                hashed_password=data["hashed_password"],
                avatar_url=data["avatar_url"],
                confirmed=data["confirmed"],
                role=data.get("role", "user"),
            )
            return user
    except Exception:
        pass

    user_service = UserService(db)
    user = await user_service.get_user_by_username(username)
    if user is None:
        raise credentials_exeption

    try:
        user_data = {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "hashed_password": user.hashed_password,
            "avatar_url": user.avatar_url,
            "confirmed": user.confirmed,
            "role": user.role.value if hasattr(user, "role") and user.role else "user",
        }
        await redis_client.setex(cache_key, 3600, json.dumps(user_data))
    except Exception:
        pass

    return user


async def create_email_token(data: dict):
    to_encode = data.copy()
    now = datetime.now(UTC)
    expire = now + timedelta(days=7)
    to_encode.update({"iat": now, "exp": expire})

    token = jwt.encode(to_encode, config.JWT_SECRET, algorithm=config.JWT_ALGORITHM)
    return token


async def create_reset_token(data: dict):
    to_encode = data.copy()
    now = datetime.now(UTC)
    expire = now + timedelta(hours=1)
    to_encode.update({"iat": now, "exp": expire})

    token = jwt.encode(to_encode, config.JWT_SECRET, algorithm=config.JWT_ALGORITHM)
    return token


async def get_email_from_token(token: str):
    try:
        payload = jwt.decode(
            token, config.JWT_SECRET, algorithms=[config.JWT_ALGORITHM]
        )
        email = payload.get("sub")
        return email
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Faulty token for email verification",
        )


async def get_current_admin_user(
    current_user: User = Depends(get_current_user),
):
    if current_user.role != Role.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Operation forbidden: Admin role required",
        )
    return current_user
