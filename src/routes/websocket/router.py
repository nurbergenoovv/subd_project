import json
from typing import List, Dict, Any
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter(
    tags=["websocket"],
    prefix='/ws'
)


class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[int, List[WebSocket]] = {}
        self.general_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket, category_id: int = None):
        await websocket.accept()
        if category_id is None:
            self.general_connections.append(websocket)
            print(f"WebSocket connected for general: {websocket}")
        else:
            if category_id not in self.active_connections:
                self.active_connections[category_id] = []
            self.active_connections[category_id].append(websocket)
            print(f"WebSocket connected: {websocket}")

    def disconnect(self, websocket: WebSocket, category_id: int = None):
        if category_id is None:
            self.general_connections.remove(websocket)
            print(f"WebSocket disconnected for general: {websocket}")
        else:
            if category_id in self.active_connections:
                self.active_connections[category_id].remove(websocket)
                if not self.active_connections[category_id]:
                    del self.active_connections[category_id]
            print(f"WebSocket disconnected: {websocket}")

    async def broadcast(self, message: Dict[str, Any], category_id: int = None):
        formatted_message = json.dumps({
            "action": message["action"],
            "category_id": message['category_id'],
            "data": message["data"]
        })
        if category_id is None:
            for connection in self.general_connections:
                try:
                    await connection.send_text(formatted_message)
                except Exception as e:
                    print(f"Error broadcasting message: {str(e)}")
        else:
            if category_id in self.active_connections:
                for connection in self.active_connections[category_id]:
                    try:
                        await connection.send_text(formatted_message)
                    except Exception as e:
                        print(f"Error broadcasting message: {str(e)}")


manager = ConnectionManager()


@router.websocket("/")
async def websocket_endpoint(websocket: WebSocket):
    category_id = None
    await manager.connect(websocket, category_id)
    try:
        while True:
            data = await websocket.receive_json()
            print(f"Received message: {data}")
            if "category_id" in data:
                category_id = data["category_id"]
            # Обработка входящих сообщений если необходимо
    except WebSocketDisconnect:
        manager.disconnect(websocket, category_id)
        print("WebSocket connection closed")
    except Exception as e:
        print(f"WebSocket error: {str(e)}")
