from fastapi import Depends, APIRouter, HTTPEx
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

from app.services.user import UserService, get_current_user
from app.schemas.user import UserLoginSchema, UserSchema, TokenSchema
from . import validate_api_token

router = APIRouter(prefix="/api/user", tags=["User"])


@router.post("/login", response_model=TokenSchema)
async def login(
        schema: UserLoginSchema = Depends(UserLoginSchema.as_form),
        _=Depends(validate_api_token),
        service: UserService = Depends()
):
    return await service.login(schema)


@router.get("", response_model=UserSchema)
async def get_me(
        _=Depends(validate_api_token),
        user: UserSchema = Depends(get_current_user),
):
    return user

