from typing import List

import fastapi
from fastapi import Depends
from sqlalchemy.orm import Session

from config.database.config import get_db
from users.manager import create_user, get_users
from users.schema import UserCreateSchema, UserDetailSchema

router = fastapi.APIRouter()


@router.get("/", response_model=List[UserDetailSchema])
async def read_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    users = get_users(db, skip=skip, limit=limit)
    return users


@router.post("", response_model=UserDetailSchema, status_code=201)
async def create_new_user(user: UserCreateSchema, db: Session = Depends(get_db)):
    return create_user(db=db, user=user)
