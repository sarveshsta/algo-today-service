from datetime import datetime
from typing import Optional

from pydantic import BaseModel


# Pydantic schema for request and response
class TradingDataCreate(BaseModel):
    user_id: str
    trace_candle: Optional[int] = None
    close: Optional[str] = None
    high: Optional[str] = None
    low: Optional[str] = None
    open: Optional[str] = None
    buying_multiplier: Optional[float] = None
    stop_loss_multiplier: Optional[float] = None
    sl_low_multiplier_1: Optional[float] = None
    sl_low_multiplier_2: Optional[float] = None
    trail_sl_1: Optional[float] = None
    trail_sl_2: Optional[float] = None
    modify_stop_loss_1: Optional[float] = None
    modify_stop_loss_2: Optional[float] = None


class TradingDataUpdate(TradingDataCreate):
    pass  # Same fields as TradingDataCreate

class StrategyDetailsSchema(BaseModel):
    user_id : str
    strategy_name : str
    index : str
    strike_price : float
    expiry : str
    option : str
    chart_time : str
    indicator1 :str
    indicator2 : str
    indicator3 : str
    indicator4 : str

class TradingDataResponse(BaseModel):
    id: int
    user_id: str
    trace_candle: Optional[int]
    close: Optional[str]
    high: Optional[str]
    low: Optional[str]
    open: Optional[str]
    buying_multiplier: Optional[float]
    stop_loss_multiplier: Optional[float]
    sl_low_multiplier_1: Optional[float]
    sl_low_multiplier_2: Optional[float]
    trail_sl_1: Optional[float]
    trail_sl_2: Optional[float]
    modify_stop_loss_1: Optional[float]
    modify_stop_loss_2: Optional[float]

    class Config:
        orm_mode = True


class TokenSchema(BaseModel):
    token: str
    symbol: str
    name: str
    expiry: str
    strike: str
    lotsize: str
    instrumenttype: str
    exch_seg: str
    tick_size: str

    class Config:
        from_attributes = True


class TradeDetailSchema(BaseModel):
    id: int
    user_id: str
    signal: str
    price: float
    trade_time: datetime  # You can use datetime and let FastAPI format it
    token: TokenSchema

    class Config:
        orm_mode = True


class TradeDetailsSchema(BaseModel):
    id: int
    user_id: str
    signal: str
    price: float
    trade_time: datetime  # You can use datetime and let FastAPI format it
    token_id: str

    class Config:
        orm_mode = True


class ExpirySchema(BaseModel):
    token: str
    symbol: str
    index: str
    expiry: str

    class Config:
        from_attributes = True


class IndexData(BaseModel):
    index: str
    strike_price: int
    expiry: str
    option: str
    chart_time: str
    quantity: int | None
    trading_amount: int | None

    class Config:
        from_attributes = True


class StartStrategySchema(BaseModel):
    user_id: str
    strategy_id: str
    index_list: list[IndexData]
    target_profit: int

    class Config:
        from_attributes = True


class Order(BaseModel):
    unique_order_id: str
    symboltoken: str
    signal: str
    price: float
    status: str
    quantity: str
    ordertype: str
    producttype: str
    duration: str
    stoploss: float
    average_price: float
    exchange_order_id: str
    transactiontime: int

    class Config:
        from_attributes = True
