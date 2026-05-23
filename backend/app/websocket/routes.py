import json

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.core.security import decode_token
from app.websocket.manager import ws_manager

router = APIRouter()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token: str = ""):
    if not token:
        await websocket.close(code=4001)
        return
    try:
        payload = decode_token(token)
        user_id = int(payload["sub"])
    except Exception:
        await websocket.close(code=4001)
        return

    await ws_manager.connect(user_id, websocket)
    try:
        while True:
            data = await websocket.receive_text()
            try:
                payload = json.loads(data)
            except json.JSONDecodeError:
                await websocket.send_text('{"type":"ack","message":"消息已接收"}')
                continue

            event_type = payload.get("type")
            target_user_id = payload.get("to_user_id")
            if event_type in {
                "call_offer",
                "call_answer",
                "call_ice",
                "call_reject",
                "call_hangup",
            } and isinstance(target_user_id, int):
                forward_payload = {
                    "type": event_type,
                    "from_user_id": user_id,
                    "payload": payload.get("payload"),
                }
                await ws_manager.send_to_user(target_user_id, forward_payload)
                continue

            await websocket.send_text('{"type":"ack","message":"消息已接收"}')
    except WebSocketDisconnect:
        ws_manager.disconnect(user_id, websocket)
