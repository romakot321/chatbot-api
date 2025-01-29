from pydantic import BaseModel, Field, AliasChoices


class AIMessageSchema(BaseModel):
    role: str = "user"
    content: str = Field(validation_alias=AliasChoices("content", "text"))
