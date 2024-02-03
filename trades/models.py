from datetime import datetime

from sqlalchemy import Column, Date, String
from sqlalchemy.orm import declarative_base

from core.mixins import CoreBaseModel

Base = declarative_base()


class TokenModel(CoreBaseModel, Base):
    __tablename__ = "tokens"

    token = Column(String, unique=True, primary_key=True)
    symbol = Column(String, index=True)
    name = Column(String)
    expiry_date = Column(Date, index=True)
    strike = Column(String)
    lotsize = Column(String)
    instrumenttype = Column(String)
    exch_seg = Column(String)
    tick_size = Column(String)

    @property
    def expiry(self) -> str:
        return self.expiry_date.strftime("%d%b%Y")

    @expiry.setter
    def expiry(self, value) -> None:
        self.expiry_date = datetime.strptime(value, "%d%b%Y").date()
