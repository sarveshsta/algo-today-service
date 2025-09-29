from fastapi import WebSocket
from typing import List, Dict

connected_clients: Dict[str, List[WebSocket]] = {}

async def register_client(websocket: WebSocket, user_id: str):
    await websocket.accept()
    if user_id not in connected_clients:
        connected_clients[user_id] = []
    connected_clients[user_id].append(websocket)

def unregister_client(websocket: WebSocket, user_id: str):
    if user_id in connected_clients and websocket in connected_clients[user_id]:
        connected_clients[user_id].remove(websocket)
        if not connected_clients[user_id]:  # cleanup if empty
            del connected_clients[user_id]

async def broadcast_trade_saved(trade_data: dict):
    message = {
        "key": "TRADE_SAVED",  # Frontend will use this key to reload trades
        "payload": trade_data
    }
    disconnected_clients = []

    for user_id, websockets in connected_clients.items():
        for ws in websockets:
            try:
                await ws.send_json(message)
            except:
                disconnected_clients.append((ws, user_id))

    for ws, user_id in disconnected_clients:
        unregister_client(ws, user_id)

async def broadcast_strategy_status(strategy_status: dict):
    message = {
        "key": "STRATEGY_RUNNING",  # Frontend will use this key to reload trades
        "payload": strategy_status
    }
    disconnected_clients = []

    for user_id, websockets in connected_clients.items():
        for ws in websockets:
            try:
                await ws.send_json(message)
            except:
                disconnected_clients.append((ws, user_id))

    for ws, user_id in disconnected_clients:
        unregister_client(ws, user_id)

async def send_log(user_id: str, message: str):
    if user_id not in connected_clients:
        return
    disconnected_clients = []
    for client in connected_clients[user_id]:
        try:
            await client.send_text(message)
        except:
            disconnected_clients.append(client)

    for client in disconnected_clients:
        unregister_client(client, user_id)
