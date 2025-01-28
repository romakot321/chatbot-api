from pydantic import BaseModel, ConfigDict
from fastapi import Form


class UserSchema(BaseModel):
    id: int
    external_id: str
    app_bundle: str
    balance: int

    model_config = ConfigDict(from_attributes=True)


class UserLoginSchema(BaseModel):
    external_id: str
    app_bundle: str

    @classmethod
    def as_form(
        cls,
        external_id: str | None = Form(None),
        app_bundle: str | None = Form(None),
        username: str | None = Form(None),
        password: str | None = Form(None),
    ):
        return cls(external_id=external_id or username, app_bundle=app_bundle or password)


class TokenSchema(BaseModel):
    access_token: str
    token_type: str = "Bearer"

