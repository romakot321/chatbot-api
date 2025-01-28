from fastapi import Depends, APIRouter
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

from app.services.user import UserService, get_current_user
from app.schemas.user import UserLoginSchema, UserSchema

router = APIRouter(prefix="/api/user", tags=["User"])


@router.post("/login")
async def login(
        schema: UserLoginSchema = Depends(UserLoginSchema.as_form),
        service: UserService = Depends()
):
    return await service.login(schema)


@router.get("", response_model=UserSchema)
async def get_me(
        user: UserSchema = Depends(get_current_user),
):
    return user

