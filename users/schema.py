from typing import Optional

from pydantic import BaseModel


class UserCreateSchema(BaseModel):
    broker_account_id: str
    access_token: str
    refresh_token: str
    feed_token: Optional[str]
    access_token_expires: int

    class Config:
        from_attributes = True


class UserDetailSchema(BaseModel):
    id: str
    broker_account_id: str
    feed_token: Optional[str]
    access_token_expires: int

    class Config:
        from_attributes = True
