from pydantic import BaseModel, ConfigDict


class ChatCreateSchema(BaseModel):
    name: str


class ChatSchema(BaseModel):
    id: str
    name: str
    user_id: int


class ChatGenerateSchema(BaseModel):
    text: str


class ChatGenerateResponseSchema(BaseModel):
    text: str


class ChatMessageAuthSchema(BaseModel):
    token: str
    chat_id: str

