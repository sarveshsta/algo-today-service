from fastapi import FastAPI
from redis_om import get_redis_connection

import users.models as user_models
from config.constants import REDIS_HOST, REDIS_PASSWORD, REDIS_PORT
from config.database.config import engine
from users import route as user_route

user_models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Algo Trading Backend Service",
    description="This service is responsible for trading",
    version="0.0.1",
    contact={
        "name": "Keval",
        "email": "kevalrajpal2580@gmail.com",
    },
    license_info=None,
)

redis = get_redis_connection(
    host=REDIS_HOST,
    port=REDIS_PORT,
    password=REDIS_PASSWORD,
    decode_responses=True,
)


app.include_router(user_route.router, prefix="/users", tags=["users"])
