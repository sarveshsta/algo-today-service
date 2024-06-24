from datetime import datetime

from sqlalchemy import Column, Integer, String, Float, JSON, DateTime, ForeignKey, Date
from sqlalchemy.orm import declarative_base
from datetime import datetime
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


class TradeDetails(CoreBaseModel, Base):
    __tablename__ = "trades"

    id = Column(Integer, primary_key=True, autoincrement=True)
    token = Column(String, ForeignKey("tokens.token"), nullable=False)
    signal = Column(String, nullable=False)
    price = Column(Float, nullable=False)
    trade_time = Column(DateTime, default=datetime.now())

class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(String, index=True, unique=True)
    unique_order_id = Column(String, index=True, unique=True)
    token = Column(String)
    signal = Column(String)
    price = Column(Float)
    status = Column(String)
    quantity = Column(Integer)
    ordertype = Column(String)
    producttype = Column(String)
    duration = Column(String)
    stoploss = Column(Float)
    status = Column(String)
    transactiontime = Column(DateTime)
    full_response = Column(JSON)
    created_at = Column(DateTime, default=datetime.now())
    updated_at = Column(DateTime, default=datetime.now(), onupdate=datetime.now())

    def calculate_total_value(self):
        return self.price * self.quantity