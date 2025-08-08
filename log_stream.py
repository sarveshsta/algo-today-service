from fastapi import WebSocket
from typing import List

connected_clients: List[WebSocket] = []

async def register_client(websocket: WebSocket):
    await websocket.accept()
    connected_clients.append(websocket)

def unregister_client(websocket: WebSocket):
    if websocket in connected_clients:
        connected_clients.remove(websocket)

async def broadcast_trade_saved(trade_data: dict):
    message = {
        "key": "TRADE_SAVED",  # Frontend will use this key to reload trades
        "payload": trade_data
    }
    disconnected_clients = []
    for client in connected_clients:
        try:
            await client.send_json(message)
        except:
            disconnected_clients.append(client)
    for client in disconnected_clients:
        unregister_client(client)
        

async def send_log(message: str):
    for client in connected_clients:
        try:
            await client.send_text(message)
        except:
            pass
