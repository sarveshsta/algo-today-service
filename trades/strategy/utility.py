from trades.models import Order
from fastapi import Depends
from sqlalchemy.orm import Session
from config.database.config import get_db

async def save_order(order_response: dict, full_order_response: dict, db: Session = Depends(get_db)):
    order = Order(
        order_id = order_response['data']['order_id'],
        unique_order_id = full_order_response['data'].get('unique_order_id'),
        token = full_order_response['data'].get('token'),
        signal = full_order_response['data'].get('signal'),
        price = full_order_response['data'].get('price'),
        status = full_order_response['data'].get('status'),
        quantity = full_order_response['data'].get('quantity'),
        ordertype = full_order_response['data'].get('ordertype'),
        producttype = full_order_response['data'].get('producttype'),
        duration = full_order_response['data'].get('duration'),
        stoploss = full_order_response['data'].get('stoploss'),
        status = full_order_response['data'].get('status'),
        transactiontime = full_order_response['data'].get('transactiontime'),
        full_response = full_order_response['data'].get('full_response')
    )
    db.add(order)
    await db.commit()