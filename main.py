import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI

import trades.models as trades_models
import users.models as user_models
from config.constants import API_KEY, CLIENT_CODE, PASSWORD, REDIS_HOST, REDIS_PASSWORD, REDIS_PORT, TOKEN_CODE
from config.database.config import engine
from core.events import NotEventException, handle_activity
from core.redis import PubSubClient
from trades import route as trade_route
from trades.stream import WSApp
from users import route as user_route

user_models.Base.metadata.create_all(bind=engine)
trades_models.Base.metadata.create_all(bind=engine)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # things to do on start-ups
    channel_name = "trade-services"
    pubsub_client = PubSubClient()
    pubsub_client.create_connection(host=REDIS_HOST, port=REDIS_PORT, password=REDIS_PASSWORD)
    pubsub_client.create_psub()
    await pubsub_client.subscribe(channel_name)

    token_list = [{"exchangeType": 2, "tokens": ["36454"]}]
    trade_websocket = WSApp(
        api_key=API_KEY,
        token_code=TOKEN_CODE,
        client_code=CLIENT_CODE,
        password=PASSWORD,
        token_listener=token_list,
        pubsub=pubsub_client,
    )

    trade_websocket.connect()

    # execute in background thread
    reader_task = asyncio.create_task(message_listener(pubsub_client))

    yield
    # things to do on shutdown
    print("shutting down")
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
