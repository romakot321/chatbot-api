from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from fastapi import HTTPException
from pydantic import ValidationError

from app.schemas.chat import ChatCreateSchema, ChatSchema, ChatMessageAuthSchema
from app.schemas.chat import ChatGenerateSchema
from app.schemas.user import UserSchema
from app.services.chat import ChatService, ChatWorker
from app.services.user import UserService, get_current_user
from . import validate_api_token

router = APIRouter(prefix="/api/chat", tags=["Chat"])


async def _authenticate_connection(
        websocket: WebSocket,
        chat_service: ChatService = Depends(),
        user_service: UserService = Depends()
) -> ChatWorker | None:
    text = await websocket.receive_text()
    try:
        msg = ChatMessageAuthSchema.model_validate_json(text)
    except ValidationError:
        await websocket.send_text("Invalid input data")
        await websocket.close(code=1008)
        return None

    try:
        user = await user_service.get_by_token(msg.token)
        worker = await chat_service.connect(msg.chat_id, user)
    except HTTPException:
        await websocket.send_text("Invalid credentials")
        await websocket.close(code=1008)
        return None
    await websocket.send_text("OK")
    return worker


async def _handle_connection(
        websocket: WebSocket,
        worker
):
    while True:
        data = await websocket.receive_json()
        print("Received ws", data)
        try:
            msg = ChatGenerateSchema.model_validate(data)
        except ValidationError as e:
            await websocket.send_text("Invalid input data")
            print(e)
            continue

        response = await worker.new_message(msg)
        await websocket.send_json(response.model_dump())


@router.post("", response_model=ChatSchema, status_code=201)
async def create_chat(
        schema: ChatCreateSchema,
        _=Depends(validate_api_token),
        user: UserSchema = Depends(get_current_user),
        service: ChatService = Depends()
):
    return await service.create(schema, user)


@router.get("", response_model=list[ChatSchema])
async def get_my_chats(
        user: UserSchema = Depends(get_current_user),
        service: ChatService = Depends()
        _=Depends(validate_api_token),
):
    return await service.list_user_chats(user.id)


@router.websocket("/conversation")
async def connect_to_chat(
        websocket: WebSocket,
        chat_service: ChatService = Depends(),
        user_service: UserService = Depends()
):
    await websocket.accept()
    worker = await _authenticate_connection(websocket, chat_service, user_service)
    if worker is None:
        return

    try:
        await _handle_connection(websocket, worker)
    except WebSocketDisconnect:
        await chat_service.disconnect(worker.chat_id)

