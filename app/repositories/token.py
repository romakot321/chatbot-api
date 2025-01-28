from datetime import datetime, timedelta, timezone
from typing import Annotated

import jwt
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jwt.exceptions import InvalidTokenError
from passlib.context import CryptContext
from pydantic import BaseModel


class TokenData(BaseModel):
    user_id: int


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/user/login")


class TokenRepository:
    SECRET_KEY = "replaceme"  # openssl rand -hex 32
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 12 * 60

    @classmethod
    def create_access_token(
            cls,
            user_id: int,
            expires_delta: timedelta | None = None
    ) -> str:
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(minutes=15)

        to_encode = {"exp": expire, "sub": str(user_id)}
        encoded_jwt = jwt.encode(to_encode, cls.SECRET_KEY, algorithm=cls.ALGORITHM)
        return encoded_jwt

    @classmethod
    def parse_access_token(cls, token: str) -> TokenData | None:
        """Return None if token is invalid"""
        try:
            payload = jwt.decode(token, cls.SECRET_KEY, algorithms=[cls.ALGORITHM])
            user_id = payload.get("sub")
            if user_id is None:
                return None
        except InvalidTokenError:
            return None
        token_data = TokenData(user_id=int(user_id))
        return token_data

