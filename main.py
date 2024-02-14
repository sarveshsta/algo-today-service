import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI

import trades.models as trades_models
import users.models as user_models
from config.constants import REDIS_HOST, REDIS_PASSWORD, REDIS_PORT
from config.database.config import engine
from core.redis import PubSubClient
from trades import route as trade_route
from users import route as user_route

user_models.Base.metadata.create_all(bind=engine)
trades_models.Base.metadata.create_all(bind=engine)


@asynccontextmanager
async def lifespan(app: FastAPI):
    channel_name = "trade-services"
    pubsub_client = PubSubClient()
    pubsub_client.create_connection(host=REDIS_HOST, port=REDIS_PORT, password=REDIS_PASSWORD)
    pubsub_client.create_psub()
    await pubsub_client.subscribe(channel_name)

    reader_task = asyncio.create_task(message_listener(pubsub_client))

    yield
    await pubsub_client.unsubscribe_from_channel(channel_name)
    reader_task.cancel()


async def message_listener(pubsub_client: PubSubClient):
    async for message in pubsub_client.listen():
        pubsub_client.message_handler(message)


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
