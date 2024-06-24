import asyncio
from contextlib import asynccontextmanager
import uvicorn

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
from trades.strategy import my_strategy as strategy_route

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
        "name": "Keval",
        "email": "kevalrajpal2580@gmail.com",
    },
    license_info=None,
    lifespan=lifespan,
)


app.include_router(user_route.router, prefix="/users", tags=["users"])
app.include_router(trade_route.router, prefix="/tokens", tags=["tokens"])
app.include_router(strategy_route.router, prefix="/strategy")

@app.get("/", tags=["Root"])
async def read_root():
    return {"message": "Welcome to the API!"}

# from trades.managers import start_strategy, stop_pause_strategy
# @app.get("/run")
# def run_strategy():
#     print("data")
#     response = start_strategy()
#     if response:
#         return JSONResponse({"success": True}, status_code=200)
#     return JSONResponse({"success": False}, status_code=400)

# @app.get("/stop")
# def exit_strategy():
#     print("stop or pause", asyncio.tasks.all_tasks())
#     response = stop_pause_strategy("strategy_1")
#     if response:
#         return JSONResponse({"loop exit success": True}, status_code=200)
#     return JSONResponse({"loop exit success": False}, status_code=400)

origins = [
    "http://localhost.tiangolo.com",
    "https://localhost.tiangolo.com",
    "http://localhost",
    "http://localhost:3000",
    "http://15.206.153.177:8000"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=5000, log_level="info")