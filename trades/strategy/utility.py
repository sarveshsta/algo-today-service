import os, csv
import aiosmtplib
from fastapi import Depends
from trades.models import Order
from sqlalchemy.orm import Session
from config.database.config import get_db
from email.message import EmailMessage
from email.utils import formatdate
from dotenv import load_dotenv

load_dotenv()
class Envs:
    USERNAME = os.getenv('USERNAME')
    PASSWORD = os.getenv('PASSWORD')
    PORT = os.getenv('PORT')
    SERVER = os.getenv('SERVER')

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
        transactiontime = full_order_response['data'].get('transactiontime'),
        full_response = full_order_response['data'].get('full_response')
    )
    db.add(order)
    await db.commit()

async def place_order_mail(db: Session = Depends(get_db)):
    orders = db.query(Order).all()

    with open("today_orders.csv", "w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["symboltoken", "signal", "price", "status", "quantity", "ordertype", "stoploss", "average_price", "transactiontime"])
        for order in orders:
            writer.writerow([
                order.symboltoken, order.signal, order.price, order.status, order.quantity, order.ordertype, order.producttype, order.duration, order.stoploss, order.average_price, order.exchange_order_id, order.transactiontime
            ])

    await send_email_async("New Order Place", "Please check attached file for today's all orders", Envs.USERNAME, "receiver@yopmail.com", csvfile)
    return {"message": "Data is retrieved and email sent"}

async def send_email_async(subject, message, sender, receiver, csv_file):
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = receiver
    msg["Date"] = formatdate(localtime=True)
    msg.set_content(message)

    with open(csv_file, "rb") as f:
        file_data = f.read()
        msg.add_attachment(file_data, maintype='application', subtype='octet-stream', filename=csv_file)    
    try:
        client = aiosmtplib.SMTP(hostname=Envs.SERVER, port=int(Envs.PORT))
        await client.connect()
        await client.login(Envs.USERNAME, Envs.PASSWORD)
        await client.send_message(msg)
        await client.quit()
        return True
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False