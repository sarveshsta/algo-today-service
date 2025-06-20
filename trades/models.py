from datetime import datetime
import uuid
from sqlalchemy import JSON, Column, Date, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import declarative_base, relationship
from config.database.config import Base
from core.mixins import CoreBaseModel
from sqlalchemy.dialects.postgresql import UUID



class TokenModel(Base):
    __tablename__ = "algo_app_token"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    token = Column(String, unique=True)
    symbol = Column(String)
    name = Column(String)
    expiry_date = Column(Date)
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
        if value:
            self.expiry_date = datetime.strptime(value, "%d%b%Y").date()
        else:
            self.expiry_date = None


class TradeDetails(Base):
    __tablename__ = "algo_app_tradedetails"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String, index=True)
    signal = Column(String, nullable=False)
    price = Column(Float, nullable=False)
    trade_time = Column(DateTime, default=datetime.now)

    token_id = Column(UUID(as_uuid=True), ForeignKey("algo_app_token.id"), nullable=False)

    token = relationship("TokenModel", backref="trade_details")




class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True)
    order_id = Column(String, index=True, unique=True)
    unique_order_id = Column(String, index=True, unique=True)
    symboltoken = Column(String)
    signal = Column(String)
    price = Column(Float)
    status = Column(String)
    quantity = Column(Integer)
    ordertype = Column(String)
    producttype = Column(String)
    duration = Column(String)
    stoploss = Column(Float)
    average_price = Column(Float)
    transactiontime = Column(DateTime)
    exchange_order_id = Column(String)
    full_response = Column(JSON)
    created_at = Column(DateTime, default=datetime.now())
    updated_at = Column(DateTime, default=datetime.now(), onupdate=datetime.now())

    def calculate_total_value(self):
        return self.price * self.quantity


class StrategyValue(Base):
    __tablename__ = "strategy"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True)
    strategy_name = Column(String, index=True, unique=True)
    index = Column(String, index=True, unique=False)
    strike_price = Column(Float)
    expiry = Column(String)
    option = Column(String)
    chart_time = Column(String)
    indicator1 = Column(String)
    indicator2 = Column(String)
    indicator3 = Column(String)
    indicator4 = Column(String)


class TradingData(Base):
    __tablename__ = "tradingdata"

    id = Column(Integer, primary_key=True, index=True)
    trace_candle = Column(Integer)
    close = Column(String)
    high = Column(String)
    low = Column(String)
    open = Column(String)
    buying_multiplier = Column(Float)
    stop_loss_multiplier = Column(Float)
    sl_low_multiplier_1 = Column(Float)
    sl_low_multiplier_2 = Column(Float)
    trail_sl_1 = Column(Float)
    trail_sl_2 = Column(Float)
    modify_stop_loss_1 = Column(Float)
    modify_stop_loss_2 = Column(Float)


