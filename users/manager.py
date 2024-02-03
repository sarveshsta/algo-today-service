from fastapi import Depends
from sqlalchemy.orm import Session

from config.database.config import get_db
from users.models import UserModel
from users.schema import UserCreateSchema


def get_users(db: Session = Depends(get_db), skip: int = 0, limit: int = 100):
    users = db.query(UserModel).offset(skip).limit(limit).all()
    return users


def create_user(db: Session, user: UserCreateSchema):
    db_user = UserModel(
        access_token=user.access_token,
        refresh_token=user.refresh_token,
        feed_token=user.feed_token,
        broker_account_id=user.broker_account_id,
        access_token_expires=user.access_token_expires,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user
