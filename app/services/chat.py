from fastapi import Depends, HTTPException

from app.schemas.chat import ChatCreateSchema, ChatSchema
from app.schemas.chat import ChatGenerateSchema, ChatGenerateResponseSchema
from app.schemas.user import UserSchema
from app.schemas.ai import AIMessageSchema
from app.repositories.chat import ChatRepository
from app.repositories.ai import AIRepository

_workers = []


class ChatWorker:
    def __init__(self, chat_id: str, ai_repository: ChatRepository, messages: list = None):
        self.chat_id = chat_id
        self.ai_repository = ai_repository
        self.messages: list[AIMessageSchema] = messages if messages else []

    def _add_message(self, text: str):
        self.messages.append(AIMessageSchema(content=text))

    async def new_message(self, schema: ChatGenerateSchema) -> ChatGenerateResponseSchema:
        self._add_message(schema.text)
        text = await self.ai_repository.generate(self.messages)
        return ChatGenerateResponseSchema(text=text)

    def list_messages(self) -> list[ChatGenerateSchema]:
        return [ChatGenerateSchema(text=msg.content) for msg in self.messages]


class ChatService:
    def __init__(
            self,
            chat_repository: ChatRepository = Depends(),
            ai_repository: AIRepository = Depends()
    ):
        self.chat_repository = chat_repository
        self.ai_repository = ai_repository

    async def create(self, schema: ChatCreateSchema, creator: UserSchema) -> ChatSchema:
        chat = await self.chat_repository.create(user_id=creator.id, name=schema.name)
        return ChatSchema.model_validate(chat)

    async def list_user_chats(self, user_id: int) -> list[ChatSchema]:
        chats = await self.chat_repository.list_user_chats(user_id)
        return [ChatSchema.model_validate(chat) for chat in chats]

    async def connect(self, chat_id: str, user: UserSchema) -> ChatWorker:
        global _workers
        chat = await self.chat_repository.get(chat_id)
        if chat is None:
            raise HTTPException(404)
        if chat.user_id != user.id:
            raise HTTPException(401)

        history = await self.chat_repository.get_history(chat_id)
        worker = ChatWorker(chat_id=chat_id, ai_repository=ai_repository, messages=history)
        _workers.append(worker)
        return worker

    async def disconnect(self, chat_id: str):
        worker = [w for w in _workers if w.chat_id == chat_id]
        if not worker:
            return
        worker = worker[0]

        await self.chat_repository.save_history(chat_id, worker.list_messages())

