from fastapi import FastAPI

import users.models as user_models
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

app.include_router(user_route.router, prefix="/users", tags=["users"])


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
