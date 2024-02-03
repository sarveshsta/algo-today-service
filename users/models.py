from sqlalchemy import Column, Integer, String

from core.mixins import Base, CoreBaseModel


class UserModel(CoreBaseModel, Base):
    __tablename__ = "users"

    access_token_encrypted = Column(String)
    refresh_token_encrypted = Column(String)
    feed_token_encrypted = Column(String, nullable=True)
    broker_account_id = Column(String, unique=True, nullable=False)
    access_token_expires = Column(Integer)

    @property
    def access_token(self) -> str:
        # TODO: Decrypt the data before using it
        return self.access_token_encrypted

    @access_token.setter
    def access_token(self, value) -> None:
        # TODO: Encrypt the data before storing it
        self.access_token_encrypted = value

    @property
    def refresh_token(self) -> str:
        # TODO: Decrypt the data before using it
        return self.refresh_token_encrypted

    @refresh_token.setter
    def refresh_token(self, value) -> None:
        # TODO: Encrypt the data before storing it
        self.refresh_token_encrypted = value

    @property
    def feed_token(self) -> str:
        # TODO: Decrypt the data before using it
        return self.feed_token_encrypted

    @feed_token.setter
    def feed_token(self, value) -> None:
        # TODO: Encrypt the data before storing it
        self.feed_token_encrypted = value
