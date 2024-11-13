import asyncio
from contextlib import asynccontextmanager
import uvicorn
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

import trades.models as trades_models
import users.models as user_models
from config.constants import (
    API_KEY,
    CLIENT_CODE,
    PASSWORD,
    REDIS_HOST,
    REDIS_PASSWORD,
    REDIS_PORT,
    SERVICE_NAME,
    TOKEN_CODE,
)
from config.database.config import engine
from core.events import NotEventException, handle_activity
from core.redis import PubSubClient
from trades import route as trade_route
from trades.stream import WSApp
from users import route as user_route
from trades.strategy import optimization as strategy_route

user_models.Base.metadata.create_all(bind=engine)
trades_models.Base.metadata.create_all(bind=engine)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # things to do on start-ups
    channel_name = SERVICE_NAME
    app.state.channel_name = channel_name

    pubsub_client = PubSubClient()
    pubsub_client.create_connection(host=REDIS_HOST, port=REDIS_PORT, password=REDIS_PASSWORD)
    pubsub_client.create_psub()
    await pubsub_client.subscribe(channel_name)

    token_list = [{"exchangeType": 2, "tokens": ["67567"]}]
    trade_websocket = WSApp(
        api_key=API_KEY,
        token_code=TOKEN_CODE,
        client_code=CLIENT_CODE,
        password=PASSWORD,
        token_listener=token_list,
        pubsub=pubsub_client,
    )

    # execute in background thread
    reader_task = asyncio.create_task(message_listener(pubsub_client))
    trade_websocket.connect()

    yield
    # things to do on shutdown
    trade_websocket.close_connection()
    await pubsub_client.unsubscribe_from_channel(channel_name)
    reader_task.cancel()


async def message_listener(pubsub_client: PubSubClient):
    async for message in pubsub_client.listen():
        try:
            handle_activity(message, pubsub_client)
        except NotEventException:
            pass


app = FastAPI(
    title="Algo Trading Backend Service",
    description="This service is responsible for trading",
    version="0.0.1",
    contact={
        "name": "Sarvesh",
        "email": "sarvesh91199@gmail.com",
    },
    license_info=None,
    lifespan=lifespan,
)


app.include_router(user_route.router, prefix="/users", tags=["Users"])
app.include_router(trade_route.router, prefix="/tokens", tags=["Tokens"])
app.include_router(strategy_route.router, prefix="/strategy", tags=["Strategy"])

@app.get("/", tags=["Root"])
async def read_root():
    return {"message": "Welcome to the API!"}

origins = ["localhost:3000",
           "http://127.0.0.1:3000",
           "http://localhost:3000",
           "127.0.0.1:3000",
           "http://65.2.33.152",
           "*",
           'https://b420-2405-201-301d-f0b0-554d-492c-820a-e3c0.ngrok-free.app/']

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
PORT: int  = 5000

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=PORT, log_level="info")