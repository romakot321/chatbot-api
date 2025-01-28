from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from pydantic import ValidationError

from app.schemas.chat import ChatCreateSchema, ChatSchema, ChatMessageAuthSchema
from app.schemas.chat import ChatGenerateSchema
from app.schemas.user import UserSchema
from app.services.chat import ChatService, ChatWorker
from app.services.user import UserService, get_current_user

router = APIRouter(prefix="/api/chat", tags=["Chat"])


async def _authenticate_connection(
        websocket: WebSocket,
        user: UserSchema = Depends(get_current_user),
        chat_service: ChatService = Depends(),
        user_service: UserService = Depends()
) -> ChatWorker | None:
    text = await websocket.receive_text()
    try:
        msg = ChatMessageAuthSchema.model_validate_json(text)
    except ValidationError:
        await websocket.close(code=1008)
        return None

    try:
        user = await user_service.get_by_token(msg.token)
        worker = await chat_service.connect(msg.chat_id, user)
    except HTTPException:
        await websocket.close(code=1008)
        return None
    return worker


async def _handle_connection(
        websocket: WebSocket,
):
    while True:
        data = await websocket.receive_text()
        try:
            msg = ChatGenerateSchema.model_validate(data)
        except ValidationError:
            await websocket.send_text("Invalid data format")
            continue

        response = await worker.new_message(msg)
        await websocket.send_json(response.model_dump())


@router.post("", response_model=ChatSchema)
async def create_chat(
        schema: ChatCreateSchema,
        user: UserSchema = Depends(get_current_user),
        service: ChatService = Depends()
):
    return await service.create(schema, user)


@router.get("", response_model=list[ChatSchema])
async def get_my_chats(
        user: UserSchema = Depends(get_current_user),
        service: ChatService = Depends()
):
    return await service.list_user_chats(user.id)


@router.websocket("/conversation")
async def connect_to_chat(
        websocket: WebSocket,
        user: UserSchema = Depends(get_current_user),
        chat_service: ChatService = Depends(),
        user_service: UserService = Depends()
):
    await websocket.accept()
    worker = await _authenticate_connection(user, websocket, chat_service, user_service)
    if worker is None:
        return

    try:
        await _handle_connection(websocket)
    except WebSocketDisconnect:
        await chat_service.disconnect(worker.chat_id)

