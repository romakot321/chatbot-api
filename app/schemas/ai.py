from pydantic import BaseModel


class AIMessageSchema(BaseModel):
    role: str = "user"
    content: str
