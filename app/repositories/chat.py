from fastapi import Depends
from uuid import uuid4
from redis.asyncio import Redis
from pydantic import BaseModel, ValidationError

from app.schemas.chat import ChatGenerateSchema
from app.db.redis import get_redis_session


class RedisModel(BaseModel):
    pass

    def dump(self) -> dict:
        state = {}
        for key, value in self.model_dump().items():
            if isinstance(value, int):
                value = str(value)
            state[key] = value
        return state

    @classmethod
    def validate(cls, state: dict):
        raise NotImplementedError


class RedisChatSchema(RedisModel):
    user_id: int
    name: str

    def dump(self) -> dict:
        state = {}
        for key, value in self.model_dump().items():
            if isinstance(value, int):
                value = str(value)
            state[key] = value
        return state

    @classmethod
    def validate(cls, state):
        if not isinstance(state, dict):
            raise ValueError()
        return cls(user_id=int(state.get("user_id") or state.get(b"user_id")), name=(state.get("name") or state.get(b"name")))


class RedisChatMessageSchema(RedisModel):
    text: str

    @classmethod
    def validate(cls, state):
        if not isinstance(state, dict):
            raise ValueError()
        return cls(text=(state.get('text') or state.get(b'text')))


class ChatRepository:
    def __init__(
            self,
            conn: Redis = Depends(get_redis_session)
    ):
        self.conn = conn

    def _generate_id(self) -> str:
        return str(uuid4())

    async def create(self, user_id: int, name: str) -> dict:
        chat_id = self._generate_id()
        schema = RedisChatSchema(user_id=user_id, name=name)
        await self.conn.hmset(chat_id, schema.dump())
        await self.conn.hmset(chat_id + "&" + str(user_id), schema.dump())
        return schema.model_dump() | {"id": chat_id}

    async def list_user_chats(self, user_id: int) -> list[dict]:
        chats = []
        async for key in self.conn.scan_iter("*&" + str(user_id)):
            schema = RedisChatSchema.validate(await self.conn.hgetall(key))
            chats.append(schema.model_dump() | {"id": key.decode().split("&")[0]})
        return chats

    async def get(self, chat_id: str) -> dict | None:
        state = await self.conn.hgetall(chat_id)
        try:
            return RedisChatSchema.validate(state).model_dump()
        except ValueError:
            return None

    async def save_history(self, chat_id: str, messages: ChatGenerateSchema):
        for i, msg in enumerate(messages):
            schema = RedisChatMessageSchema(**msg.model_dump())
            await self.conn.hmset(chat_id + ":" + str(i), schema.dump())

    async def get_history(self, chat_id: str) -> list[ChatGenerateSchema]:
        messages = []
        async for key in self.conn.scan_iter(chat_id + ":*"):
            schema = RedisChatMessageSchema.validate(await self.conn.hgetall(key))
            messages.append(ChatGenerateSchema(**schema.model_dump()))
        return messages

