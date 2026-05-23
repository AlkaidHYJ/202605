import json
from typing import Dict, Set

from fastapi.encoders import jsonable_encoder
from fastapi import WebSocket


class ConnectionManager:
    def __init__(self):
        self.active: Dict[int, Set[WebSocket]] = {}

    async def connect(self, user_id: int, websocket: WebSocket):
        await websocket.accept()
        self.active.setdefault(user_id, set()).add(websocket)

    def disconnect(self, user_id: int, websocket: WebSocket):
        if user_id in self.active:
            self.active[user_id].discard(websocket)
            if not self.active[user_id]:
                del self.active[user_id]

    async def broadcast_recall(self, message_id: int, reason: str):
        payload = json.dumps(
            {"type": "recall", "message_id": message_id, "reason": reason},
            ensure_ascii=False,
        )
        for connections in self.active.values():
            for ws in list(connections):
                try:
                    await ws.send_text(payload)
                except Exception:
                    pass

    async def send_to_user(self, user_id: int, payload: dict):
        if user_id not in self.active:
            return
        message = json.dumps(jsonable_encoder(payload), ensure_ascii=False)
        for ws in list(self.active[user_id]):
            try:
                await ws.send_text(message)
            except Exception:
                pass

    async def send_to_users(self, user_ids: set[int], payload: dict):
        for user_id in user_ids:
            await self.send_to_user(user_id, payload)


ws_manager = ConnectionManager()
