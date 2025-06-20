from typing import Optional
from pydantic import BaseModel
from uuid import UUID

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

class UserSchema(BaseModel):
    id: UUID
    name: str
    email: str

    class Config:
        from_attributes = True



class AngelOneLoginRequest(BaseModel):
    client_code: str
    password: str
    totp_secret: str

    class Config:
        from_attributes = True