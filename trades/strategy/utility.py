import os, csv
import logging
import asyncio
import aiosmtplib
from fastapi import Depends
from trades.models import Order, StrategyValue
from sqlalchemy.orm import Session
from config.database.config import get_db
from email.message import EmailMessage
from email.utils import formatdate
from dotenv import load_dotenv
from typing import Dict, List

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SMTPEnvs:
    USERNAME = os.getenv('USERNAME')
    PASSWORD = os.getenv('PASSWORD')
    PORT = os.getenv('PORT')
    SERVER = os.getenv('SERVER')

async def save_strategy(strategy_data: dict, db: Session = Depends(get_db)):
    order = StrategyValue(
        user_id = strategy_data["user_id"],
        strategy_name = strategy_data["strategy_name"],
        index = strategy_data["index"],
        strike_price = strategy_data["strike_price"],
        expiry = strategy_data["expiry"],
        option = strategy_data["option"],
        chart_time = strategy_data["chart_time"],
    )
    db.add(order)
    await db.commit()

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

    await send_email_async("New Order Place", "Please check attached file for today's all orders", SMTPEnvs.USERNAME, "receiver@yopmail.com", csvfile)
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
        client = aiosmtplib.SMTP(hostname=SMTPEnvs.SERVER, port=int(SMTPEnvs.PORT))
        await client.connect()
        await client.login(SMTPEnvs.USERNAME, SMTPEnvs.PASSWORD)
        await client.send_message(msg)
        await client.quit()
        return True
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False
    

def async_return(result):
    obj = asyncio.Future()
    obj.set_result(result)
    return obj


class SignalTrigger:
    def __init__(self, data_provider) -> None:
        self.data_provider = data_provider
    async def signal_trigger(self, data_provider, index_info, price, quantity, signal, order_id=None):
        if signal == "BUY":
            logger.info(f"signal buy")
            # order_id, full_order_response = await async_return(data_provider.place_order(index_info[0], index_info[1], "BUY", "MARKET", price, quantity))
            # if full_order_response:
            #     order_id, full_order_response = await async_return(data_provider.place_stoploss_limit_order(index_info[0], index_info[1], quantity, price, (price*0.99)))

        elif signal == "SELL":
            logger.info(f"signal sell")
            # order_id, full_order_response = await async_return(data_provider.place_order(index_info[0], index_info[1], "SELL", "MARKET", price, quantity))

        elif signal == "STOPLOSS":
            logger.info(f"signal stoploss")
        #     order_id, full_order_response = await async_return(data_provider.modify_stoploss_limit_order(index_info[0], index_info[1], quantity, price, price*0.99, order_id))
        # await place_order_mail()
        # await save_order(order_id, full_order_response)
        return "order_id"

class FetchCandleLtpValeus:
    def __init__(self, index_candle_durations, data_provider, instruments, token):
        self.index_candle_durations = index_candle_durations
        self.data_provider = data_provider
        self.instruments = instruments
        self.gen_token = token
        self.token_value: Dict[str, token] = {}

    def fetch_ltp_data(self):
        index_ltp_values: Dict[str, float] = {}
        try:
            for instrument in self.instruments:
                data = ltp_candle_values(self.index_candle_durations, "LTP", instrument, self.data_provider, self.gen_token)
                if data[f"{str(instrument.symbol)}_sym"] is None:
                    continue
                index_ltp_values[str(instrument.symbol)] = data[f"{str(instrument.symbol)}_sym"]
                self.token_value[str(instrument.symbol)] = data[f"{str(instrument.symbol)}_token"]
                
            return (index_ltp_values, self.token_value)
        except Exception as e:
            logger.error(f"An error occurred while fetching LTP data: {e}")

    def fetch_candle_data(self):
        index_candle_data: List[tuple] = []

        # index_candle_data = {str, list}
        try:
            for instrument in self.instruments:
                data = ltp_candle_values(self.index_candle_durations, "CANDLE", instrument, self.data_provider, self.gen_token)
                if data[f"{str(instrument.symbol)}_sym"] is None:
                    continue
                index_candle_data.append((str(instrument.symbol), data[f"{str(instrument.symbol)}_sym"]))
                self.token_value[str(instrument.symbol)] = data[f"{str(instrument.symbol)}_token"]
            return (index_candle_data, self.token_value)
        except logging.exception:
            logger.error(f"An error occurred while fetching candle data")


# class ProcessData:
#     def __init__(self, index_candle_data, index_ltp_values, token_value, parameters, indicator, signal_trigger, signal, data_provider, fetch_data:FetchCandleLtpValeus):
#         self.index_candle_data: index_candle_data
#         self.token_value: token_value
#         self.parameters: parameters
#         self.indicator: indicator
#         self.signal_trigger: signal_trigger
#         self.index_ltp_values = index_ltp_values
#         self.signal = signal
#         self.data_provider = data_provider
#         self.fetch_data = fetch_data(index_candle_durations, data_provider, instruments, token)

#     async def process_data(self):
#         for index, value in self.index_candle_data:
#             await asyncio.sleep(1)
#             logger.info(f"self.token_value123: {self.token_value}")
#             self.fetch_data.fetch_candle_data()
#             if (value and self.index_ltp_values[index]) is not None:
#                 logger.info(f"token1: {self.token_value[index]}, quantity1: {self.parameters[index]}")
#                 columns = ["timestamp", "Open", "High", "Low", "Close", "Volume"]
#                 data = pd.DataFrame(value, columns=columns)
#                 latest_candle = data.iloc[1]
#                 logger.info(f"Comparing LTP {self.index_ltp_values[index]} with latest candle high {latest_candle['High']}")

#                 # Implement your comparison logic here
#                 signal, price, index_info = await async_return(
#                     self.indicator.check_indicators(data, self.token_value[index], self.index_ltp_values[index])
#                 )
#                 logger.info(f"Signal: {signal}, Price: {price}")
#                 if signal in [self.signal.BUY, self.signal.SELL, self.signal.STOPLOSS]:
#                     self.order_id = await self.signal_trigger.signal_trigger(self.data_provider, index_info, price, self.parameters[index], signal, self.order_id)
#             else:
#                 logger.info("Waiting for data...")


def ltp_candle_values(index_candle_durations, tradetype, instrument, data_provider, gen_token):
    data_dict = {}
    token = gen_token(instrument.exch_seg, instrument.token, instrument.symbol)
    data_dict[f"{str(instrument.symbol)}_token"] = token
    if tradetype == "LTP":
        ltp_data = data_provider.fetch_ltp_data(token)
        if "data" not in ltp_data.keys():
            data_dict[f"{str(instrument.symbol)}_sym"] = None
        data_dict[f"{str(instrument.symbol)}_sym"] = float(ltp_data["data"]["ltp"])
    elif tradetype == "CANDLE":
        candle_duration = index_candle_durations[instrument.symbol]
        candle_data = data_provider.fetch_candle_data(token, interval=candle_duration)
        # candle_data = async_return(candle_data)
        if candle_data is None:
            data_dict[f"{str(instrument.symbol)}_sym"] = None
        data_dict[f"{str(instrument.symbol)}_sym"] = candle_data
    return data_dict
