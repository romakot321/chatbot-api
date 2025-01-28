from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

from app.repositories.token import TokenRepository
from app.repositories.user import UserRepository
from app.schemas.user import UserLoginSchema, UserSchema, TokenSchema
from app.db.tables import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/user/login")


class UserService:
    def __init__(
            self,
            token_repository: TokenRepository = Depends(),
            user_repository: UserRepository = Depends()
    ):
        self.token_repository = token_repository
        self.user_repository = user_repository

    async def login(self, schema: UserLoginSchema) -> TokenSchema:
        model = User(external_id=schema.external_id, app_bundle=schema.app_bundle)
        model = await self.user_repository.store(model)
        token = self.token_repository.create_access_token(user_id=model.id)
        return TokenSchema(access_token=token)

    async def get(self, user_id: str, app_bundle: str) -> UserSchema:
        model = await self.user_repository.get_by_external(user_id, app_bundle)
        return UserSchema.model_validate(model)

    async def get_by_token(self, token: str) -> UserSchema:
        token_data = self.token_repository.parse_access_token(token)
        if token_data is None:
            raise HTTPException(
                status_code=401,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        user = await self.user_repository.get_by_id(token_data.user_id)
        return UserSchema.model_validate(user)


async def get_current_user(
        token: str = Depends(oauth2_scheme),
        service: UserService = Depends()
):
    return await service.get_by_token(token)


