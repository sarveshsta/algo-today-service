from cryptography.fernet import Fernet
from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base

from config.constants import ENCRYPTION_KEY
from core.mixins import CoreBaseModel

Base = declarative_base()


class UserModel(CoreBaseModel, Base):
    __tablename__ = "users"

    access_token_encrypted = Column(String)
    refresh_token_encrypted = Column(String)
    feed_token_encrypted = Column(String, nullable=True)
    broker_account_id = Column(String)
    access_token_expires = Column(Integer)

    encryption_key = bytes(ENCRYPTION_KEY, "UTF-8")

    @property
    def access_token(self) -> str:
        f = Fernet(self.encryption_key)
        return f.decrypt(self.access_token_encrypted).decode()

    @access_token.setter
    def access_token(self, value) -> None:
        f = Fernet(self.encryption_key)
        self.access_token_encrypted = f.encrypt(value.encode())

    @property
    def refresh_token(self) -> str:
        f = Fernet(self.encryption_key)
        return f.decrypt(self.refresh_token_encrypted).decode()

    @refresh_token.setter
    def refresh_token(self, value) -> None:
        f = Fernet(self.encryption_key)
        self.refresh_token_encrypted = f.encrypt(value.encode())

    @property
    def feed_token(self) -> str:
        f = Fernet(self.encryption_key)
        return f.decrypt(self.feed_token_encrypted).decode()

    @feed_token.setter
    def feed_token(self, value) -> None:
        f = Fernet(self.encryption_key)
        self.feed_token_encrypted = f.encrypt(value.encode())
