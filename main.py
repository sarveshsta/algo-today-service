from fastapi import FastAPI
from redis import Redis
from rq import Queue

import users.models as user_models
from config.constants import REDIS_HOST, REDIS_PORT
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

redis_conn = Redis(host=REDIS_HOST, port=REDIS_PORT)
task_queue = Queue("task_queue", connection=redis_conn)

app.include_router(user_route.router, prefix="/users", tags=["users"])
