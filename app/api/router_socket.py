from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict
from datetime import datetime
from app.database import save_message, get_room_history, get_session
from app.user_repo import check_user_access_to_room


class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[int, Dict[int, WebSocket]] = {}

    async def connect(self, websocket: WebSocket, room_id: int, user_id: int):
        await websocket.accept()
        if room_id not in self.active_connections:
            self.active_connections[room_id] = {}
        self.active_connections[room_id][user_id] = websocket

    def disconnect(self, room_id: int, user_id: int):
        if room_id in self.active_connections and user_id in self.active_connections[room_id]:
            del self.active_connections[room_id][user_id]
            if not self.active_connections[room_id]:
                # Удаляем комнату, если она пустая
                del self.active_connections[room_id]

    async def broadcast(self, message: str, room_id: int, sender_id: int, username: str, save_to_db: bool = True):
        if room_id in self.active_connections:
            timestamp = datetime.now().strftime("%H:%M")
            
            if save_to_db:
                await save_message(room_id, sender_id, username, message, timestamp)
            
            for user_id, connection in self.active_connections[room_id].items():
                message_with_class = {
                    "text": message,
                    "is_self": user_id == sender_id,
                    "timestamp": timestamp
                }
                await connection.send_json(message_with_class)
    
    async def send_history(self, websocket: WebSocket, room_id: int, user_id: int):
        history = await get_room_history(room_id)
        for msg in history:
            message_with_class = {
                "text": msg["message"],
                "is_self": msg["user_id"] == user_id,
                "timestamp": msg["timestamp"]
            }
            await websocket.send_json(message_with_class)


manager = ConnectionManager()
router = APIRouter(prefix="/ws/chat")


@router.websocket("/{room_id}/{user_id}")
async def websocket_endpoint(websocket: WebSocket, room_id: int, user_id: int, username: str):
    async for session in get_session():
        has_access = await check_user_access_to_room(room_id, user_id, session)
        if not has_access:
            await websocket.close(code=1008, reason="Access denied")
            return
    
    await manager.connect(websocket, room_id, user_id)
    
    # Отправляем историю сообщений при подключении
    await manager.send_history(websocket, room_id, user_id)
    
    # Уведомляем о присоединении (без сохранения системных сообщений)
    await manager.broadcast(f"{username} (ID: {user_id}) присоединился к чату.", room_id, user_id, username, save_to_db=False)
    try:
        while True:
            data = await websocket.receive_text()
            await manager.broadcast(f"{username} (ID: {user_id}): {data}", room_id, user_id, username)
    except WebSocketDisconnect:
        manager.disconnect(room_id, user_id)
        await manager.broadcast(f"{username} (ID: {user_id}) покинул чат.", room_id, user_id, username, save_to_db=False)
