from pydantic import BaseModel
from datetime import datetime


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
    trading_amount : int | None
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
