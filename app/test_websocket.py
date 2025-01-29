import asyncio
import websockets
import aiohttp
import json

base_address = "localhost:8032"


async def authenticate_websocket(websocket, chat_id: str, token: str):
    creds = json.dumps({"token": token, "chat_id": chat_id})
    await websocket.send(creds)
    resp = await websocket.recv()
    assert resp == "OK", "Invalid websocket response: " + resp


async def send_generation_request(websocket, text: str) -> str:
    data = json.dumps({"text": text})
    await websocket.send(data)
    resp = await websocket.recv()
    assert resp != "Invalid input data", resp
    return json.loads(resp)['text']


async def test_websocket(chat_id: str, token: str):
    uri = f"ws://{base_address}/api/chat/conversation"
    async with websockets.connect(uri) as websocket:
        await authenticate_websocket(websocket, chat_id, token)
        print("Authenticated to chat", chat_id)

        response = await send_generation_request(websocket, "Say this is test!")
        print(f"Received from server: {response}")
        response = await send_generation_request(websocket, "Calculate 2+2*2")
        print(f"Received from server: {response}")
        await websocket.close()


async def test_reconnect(chat_id: str, token: str):
    uri = f"ws://{base_address}/api/chat/conversation"
    async with websockets.connect(uri) as websocket:
        await authenticate_websocket(websocket, chat_id, token)
        print("Authenticated to chat", chat_id)
        response = await send_generation_request(websocket, "What i ask you before?")
        print(f"Received from server: {response}")


async def authorize(user_id: str, app_bundle: str) -> str:
    """Return access_token"""
    data = f"external_id={user_id}&app_bundle={app_bundle}"

    async with aiohttp.ClientSession() as session:
        resp = await session.post(f'http://{base_address}/api/user/login', data=data, headers={"Content-Type": "application/x-www-form-urlencoded"})
        assert resp.status in (201, 200), await resp.text()
        return (await resp.json()).get("access_token")


async def create_chat(name: str, token: str) -> str:
    """Return created chat_id"""
    data = {"name": name}

    async with aiohttp.ClientSession() as session:
        resp = await session.post(
            f'http://{base_address}/api/chat',
            json=data,
            headers={"Authorization": "Bearer " + token}
        )
        assert resp.status == 201, await resp.text()
        return (await resp.json()).get("id")


async def main():
    token = await authorize("test", "test.test.com")
    chat_id = await create_chat("Test chat", token)
    await test_websocket(chat_id, token)
    await test_reconnect(chat_id, token)


asyncio.get_event_loop().run_until_complete(main())
