import asyncio
import copy
import json
import logging
import os
import socket
from datetime import datetime, timedelta
from enum import Enum
from json.decoder import JSONDecodeError
from time import sleep
from typing import Dict, List, Tuple
from urllib.error import URLError
import threading

import fastapi
import pandas as pd
from dotenv import load_dotenv
from fastapi import HTTPException
import pyotp
import requests
from SmartApi.smartConnect import SmartConnect
from SmartApi.smartWebSocketV2 import SmartWebSocketV2


from config.database.config import SessionLocal
from trades.models import TradeDetails
from trades.schema import StartStrategySchema
from trades.strategy.utility import place_order_mail, save_order, save_strategy

router = fastapi.APIRouter()
tasks: Dict[str, asyncio.Task] = {}

load_dotenv()

db = None

INDEX_CANDLE_DATA = []

LTP_API_KEY = "ZlQnOy4h"
LTP_CLIENT_CODE = "S55329579"
LTP_PASSWORD = "4242"
LTP_TOKEN_CODE = "QRLYAZPZ6LMTH5AYILGTWWN26E"

API_KEY = "8x8RGK2s"
CLIENT_CODE = "J263557"
PASSWORD = "7753"
TOKEN_CODE = "3MYXRWJIJ2CZT6Y5PD2EU5RNNQ"

base_url = "https://apiconnect.angelbroking.com"

LIVE_FEED_JSON = {}
CORRELATION_ID = "jahsgfhjaf2"
FEED_MODE = 1


class Constants:
    def __init__(self):
        self.API_KEY = "8x8RGK2s"
        self.CLIENT_CODE = "J263557"
        self.PASSWORD = "7753"
        self.TOKEN_CODE = "3MYXRWJIJ2CZT6Y5PD2EU5RNNQ"

        self.NFO_DATA_URL = "https://margincalculator.angelbroking.com/OpenAPI_File/files/OpenAPIScripMaster.json"
        self.OPT_TYPE = "OPTIDX"

        self.EXCH_TYPE = "NFO"
        self.LTP_API_KEY = "ZlQnOy4h"
        self.LTP_CLIENT_CODE = "S55329579"
        self.LTP_PASSWORD = "4242"
        self.LTP_TOKEN_CODE = "QRLYAZPZ6LMTH5AYILGTWWN26E"

        self.TRACE_CANDLE = 8
        self.CLOSE = "Close"
        self.HIGH = "High"
        self.LOW = "Low"
        self.OPEN = "Open"

        self.BUYING_MULTIPLIER = 1.01
        self.STOP_LOSS_MULTIPLIER = 0.95

        self.SL_LOW_MULTIPLIER_1 = 0.97
        self.SL_LOW_MULTIPLIER_2 = 0.985

        self.TRAIL_SL_1 = 1.20
        self.TRAIL_SL_2 = 1.10

        self.MODITY_STOP_LOSS_1 = 1.10
        self.MODITY_STOP_LOSS_2 = 1.05


constant = Constants()

trade_data = {}

# index details
NFO_DATA_URL = "https://margincalculator.angelbroking.com/OpenAPI_File/files/OpenAPIScripMaster.json"
OPT_TYPE = "OPTIDX"
EXCH_TYPE = "NFO"

smart = SmartConnect(api_key=API_KEY)
ltp_smart = SmartConnect(api_key=LTP_API_KEY)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def write_logs(type, index, price, status, reason):
    log_dir = f"logs/trade/{datetime.today().strftime('%Y-%m-%d')}"
    datetime.today()
    log_file = os.path.join(log_dir, "logs.txt")

    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    with open(log_file, "a+") as f:
        f.write(f"Trade {type} in {index} at {price} with {status}, reason {reason} at {datetime.now()} \n")


class CandleDuration(Enum):
    ONE_MINUTE = "ONE_MINUTE"
    THREE_MINUTE = "THREE_MINUTE"
    FIVE_MINUTE = "FIVE_MINUTE"
    TEN_MINUTE = "TEN_MINUTE"


class Signal(Enum):
    BUY = 1
    MODIFY = 2
    WAITING_TO_BUY = 3
    WAITING_TO_MODIFY = 4
    NULL = 5
    SELL = 6
    WAITING_TO_SELL = 7
    WAITING_FOR_MODIFY_OR_SELL = 8


class Token:
    def __init__(self, exch_seg: str, token_id: str, symbol: str):
        self.exch_seg = exch_seg
        self.token_id = token_id
        self.symbol = symbol

    def __str__(self):
        return f"{self.exch_seg}:{self.token_id}:{self.symbol}"


class Instrument:
    def __init__(
        self,
        token: str,
        symbol: str,
        name: str,
        expiry: str,
        strike: float,
        lotsize: int,
        instrumenttype: str,
        exch_seg: str,
        tick_size: float,
    ):
        self.token = token
        self.symbol = symbol
        self.name = name
        self.expiry = expiry
        self.strike = strike
        self.lotsize = lotsize
        self.instrumenttype = instrumenttype
        self.exch_seg = exch_seg
        self.tick_size = tick_size


class InstrumentReaderInterface:
    def read_instruments(self) -> List[Instrument]:
        raise NotImplementedError("Subclasses must implement read_instruments()")


class OpenApiInstrumentReader(InstrumentReaderInterface):
    def __init__(self, url: str, tokens: List[str]):
        self.url = url
        self.tokens = tokens or []

    def read_instruments(self) -> List[Instrument]:
        try:
           
            response = requests.get(self.url)
            response.raise_for_status()
            data = response.json()
            # print(data, "data")
            # print("Raw API Response:", json.dumps(data, indent=4))
            print("Tokens to match:", self.tokens)
            with open("data.json", "w") as json_file:
                json.dump(data, json_file, indent=4)
            instruments = [Instrument(**item) for item in data if item["exch_seg"] == "NFO" and item["symbol"] in self.tokens]
        
            print("Filtered Instruments:", [vars(inst) for inst in instruments])  # Debugging line

            return instruments
        except (URLError, JSONDecodeError) as e:
            print(f"Error reading instruments from {self.url}: {e}")
            return []


class DataProviderInterface:
    def fetch_candle_data(self, token: Token, interval: str = "ONE_MINUTE", symvol: str = "") -> dict:
        raise NotImplementedError("Subclasses must implement fetch_candle_data()")

    def fetch_ltp_data(self, token: Token, interval: str = "ONE_MINUTE", symvol: str = "") -> float:
        raise NotImplementedError("Subclasses must implement fetch_ltp_data()")

    def place_order(self, symbol: str, token: str, transaction: str, ordertype: str, price: str, quantity: str):
        raise NotImplementedError("Subclasses must implement place_order()")

    def sell_order(self, symbol: str, token: str, transaction: str, ordertype: str, price: str, quantity: str):
        raise NotImplementedError("Subclasses must implement place_order()")

    def modify_stoploss_limit_order(
        self, symbol: str, token: str, quantity: str, stoploss_price: float, limit_price: float, order_id: str
    ):
        raise NotImplementedError("Subclasses must implement modify_stoploss_limit_order()")

    def place_stoploss_limit_order(self, symbol, token, quantity, stoploss_price, limit_price):
        raise NotImplementedError("Subclasses must implement place_stoploss_limit_order()")

    def check_order_status(self, uniqueOrderId=None):
        raise NotImplementedError("Subclasses must implement check_order_status()")

    def get_trade_book(self, order_id):
        raise NotImplementedError("Subclasses must implement get_trade_boo()")

    def get_order_book(self, order_id):
        raise NotImplementedError("Subclasses must implement get_order_book()")


class SmartApiDataProvider(DataProviderInterface):
    def __init__(self, smart: SmartConnect, ltpSmart: SmartConnect):
        self.__smart = smart
        self.__ltpSmart = ltpSmart

    def fetch_candle_data(self, token, interval):
        try:
            to_date = datetime.now()
            from_date = to_date - timedelta(minutes=480)
            from_date_format = from_date.strftime("%Y-%m-%d %H:%M")
            to_date_format = to_date.strftime("%Y-%m-%d %H:%M")
            historic_params = {
                "exchange": token.exch_seg,
                "symboltoken": token.token_id,
                "interval": interval,
                "fromdate": from_date_format,
                "todate": to_date_format,
            }

            res_json = self.__smart.getCandleData(historic_params)
            if not res_json or "data" not in res_json or res_json["data"] is None:
                raise ValueError("No candle data received from API")
            data = res_json["data"][::-1]
            return data
        except Exception as e:
            print("Candle data exception", e)
            raise ValueError("Failed to fetch candle data")




    def fetch_ltp_data(self, token):
        try:
            ltp_data = self.__ltpSmart.ltpData("NFO", token.symbol, token.token_id)
            print("LTP DATA.....", ltp_data)
            return ltp_data['data']['ltp']
        except Exception as e:
            print("LTP data exception", e)
            raise ValueError("Failed to fetch LTP data")

   

    def get_trade_book(self, order_id):
        sleep(3) 
        retry_count = 10 

        while retry_count > 0:
            try:
                order_book = self.__smart.tradeBook()
                
                if not order_book or "data" not in order_book or not order_book["data"]:
                    logger.warning(f"⚠ Trade book response is None or empty for order {order_id}. Retrying in 5 seconds...")
                    retry_count -= 1
                    sleep(5)  # Wait before retrying
                    continue

                for trade in order_book["data"]:
                    if trade["orderid"] == order_id:
                        logger.info(f"✅ Trade details found for order {order_id}: {trade}")
                        return order_id, trade  

                logger.warning(f"⚠ Order {order_id} not found in trade book. Retrying...")
                retry_count -= 1
                sleep(5)

            except Exception as e:
                logger.error(f"❌ Error fetching trade book: {str(e)}")
                retry_count -= 1
                sleep(5)

        logger.error(f"❌ Trade book fetch failed after multiple attempts for order {order_id}. Checking order book instead.")
        
      
        return self.get_order_book(order_id)


    def get_order_book(self, order_id):
        sleep(2) 
        retry_count = 5 

        while retry_count > 0:
            try:
                order_book = self.__smart.orderBook()
                
                if not order_book or "data" not in order_book or order_book["data"] is None:
                    logger.warning(f"⚠ Order book response is None or empty for order {order_id}. Retrying...")
                    retry_count -= 1
                    sleep(5)
                    continue 
                
                for order in order_book["data"]:
                    if order["orderid"] == order_id:
                        return order_id, order
                
                logger.warning(f"⚠ Order {order_id} not found in order book. Retrying...")
                retry_count -= 1
                sleep(5)

            except Exception as e:
                logger.error(f"❌ Error fetching order book: {str(e)}")
                retry_count -= 1
                sleep(5)

        logger.error(f"❌ Order book fetch failed after multiple attempts for order {order_id}")
        return order_id, None  
    def place_order(self, symbol, token, transaction, ordertype, price, quantity):
        if ordertype == "MARKET":
            price = 700
        try:
            orderparams = {
                "variety": "NORMAL",
                "tradingsymbol": symbol,
                "symboltoken": token,
                "transactiontype": transaction,
                "exchange": "NFO",
                "ordertype": ordertype,
                "producttype": "INTRADAY",
                "duration": "DAY",
                "price": price,
                "squareoff": "0",
                "stoploss": "0",
                "quantity": quantity,
            }
            # Method 1: Place an order and return the order ID
            order_id = self.__smart.placeOrder(orderparams)
            sleep(1)
            logger.info(f"PlaceOrder id : {order_id} ")
            order_id, i = self.get_trade_book(order_id=order_id)
            return order_id, i
        except Exception as e:
            logger.info(f"Order placement failed: {e}")
            raise ValueError(f"Stop-loss placing failed, reason: {e}")

    def sell_order(self, symbol, token, transaction, ordertype, price, quantity):
        if ordertype == "MARKET":
            price = "0"
        try:
            orderparams = {
                "variety": "NORMAL",
                "tradingsymbol": symbol,
                "symboltoken": token,
                "transactiontype": transaction,
                "exchange": "NFO",
                "ordertype": ordertype,
                "producttype": "INTRADAY",
                "duration": "DAY",
                "price": price,
                "squareoff": "0",
                "stoploss": "0",
                "quantity": quantity,
            }
            # Method 1: Place an order and return the order ID
            order_id = self.__smart.placeOrder(orderparams)
            sleep(1)
            logger.info(f"Sell-order id : {order_id} ")
            order_id, i = self.get_trade_book(order_id=order_id)
            return order_id, i
        except Exception as e:
            logger.info(f"Order placement failed: {e}")
            raise ValueError(f"Stop-loss placing failed, reason: {e}")

    def modify_stoploss_limit_order(self, symbol, token, quantity, stoploss_price, limit_price, order_id):

        try:
            if not symbol or not token or not quantity or not stoploss_price or not limit_price:
                raise ValueError("Missing required parameters")

            try:
                quantity = int(quantity)
            except ValueError:
                raise ValueError("Quantity must be an integer")

            try:
                stoploss_price = float(stoploss_price)
                limit_price = float(limit_price)
                stoploss_price = round(stoploss_price, 1)
                limit_price = round(limit_price, 1)
            except ValueError:
                raise ValueError("Stop-loss price and limit price must be numbers")

            modify_sl_order_params = {
                "orderid": str(order_id),
                "variety": "STOPLOSS",
                "tradingsymbol": str(symbol),
                "symboltoken": str(token),
                "transactiontype": "SELL",  # Selling to trigger stop-loss
                "exchange": "NFO",
                "ordertype": "STOPLOSS_LIMIT",  # Stop-loss limit order
                "producttype": "INTRADAY",
                "duration": "DAY",
                "price": str(limit_price),  # Limit price for SL-L orders
                "triggerprice": str(stoploss_price),  # Trigger price for stop-loss
                "quantity": str(quantity),
            }

            # Method 1: Place an order and return the order ID
            order_id = self.__smart.modifyOrder(modify_sl_order_params)
            logger.info(f"ORDER MODIFY ID : {order_id}")
            sleep(1)
            order_id, i = self.get_trade_book(order_id=order_id)
            return order_id, i
        except Exception as e:
            logger.info(f"Order modification failed: {e}")
            raise ValueError(f"Stop-loss modification failed, reason: {e}")

    def place_stoploss_limit_order(self, symbol, token, quantity, stoploss_price, limit_price):
        try:
            # Validate parameters
            if not symbol or not token or not quantity or not stoploss_price or not limit_price:
                raise ValueError("Missing required parameters")

            try:
                quantity = int(quantity)
            except ValueError:
                raise ValueError("Quantity must be an integer")

            try:
                stoploss_price = float(stoploss_price)
                limit_price = float(limit_price)
                stoploss_price = round(stoploss_price, 1)
                limit_price = round(limit_price, 1)
            except ValueError:
                raise ValueError("Stop-loss price and limit price must be numbers")

            # Define stop-loss limit order parameters
            stoploss_limit_order_params = {
                "variety": "STOPLOSS",
                "tradingsymbol": str(symbol),
                "symboltoken": str(token),
                "transactiontype": "SELL",  # Selling to trigger stop-loss
                "exchange": "NFO",
                "ordertype": "STOPLOSS_LIMIT",  # Stop-loss limit order
                "producttype": "INTRADAY",
                "duration": "DAY",
                "price": str(limit_price),  # Limit price for SL-L orders
                "triggerprice": str(stoploss_price),  # Trigger price for stop-loss
                "quantity": str(quantity),
            }

            # Method 1: Place an order and return the order ID
            order_id = self.__smart.placeOrder(stoploss_limit_order_params)
            logger.info(f"STOPLOSS ID: {order_id}")
            sleep(1)
            order_id, i = self.get_trade_book(order_id=order_id)
            return order_id, i
        except Exception as e:
            logger.info(f"Stop loss Order place failed: {e}")
            raise ValueError(f"Stop-loss order failed, reason: {e}")

    def check_order_status(self, uniqueOrderId):
        if not uniqueOrderId:
            return ""
        try:
            order_details = self.__smart.individual_order_details(uniqueOrderId)
            logger.info(f"order_details: {order_details}")
            return order_details["data"]["status"], order_details["data"]["text"]
        except Exception as e:
            logger.error(f"Individual order status failed due to {e}")


class IndicatorInterface:
    def check_indicators(
        self, data: pd.DataFrame, passed_token: Token, ltp_value: float, index: int = 0
    ) -> tuple[Signal, float, List[str]]:
        raise NotImplementedError("Subclasses must implement check_indicators()")


def NumberOfStocksPurchased(data, total_amount):
    lotsize = data["lotsize"]
    price = data["strike"]

    slot = lotsize * price
    no_slots = int(total_amount / slot)
    quantity_purchase = no_slots * lotsize

    return quantity_purchase

class MultiIndexStrategy(IndicatorInterface):
    def __init__(self):
        self.to_buy = False
        self.to_modify = False
        self.waiting_to_modify = False
        self.waiting_for_buy = True
        self.to_sell = False
        self.waiting_to_sell = False
        self.waiting_to_modify_or_sell = False
        self.stop_loss_price = 0.0
        self.price = 0.0
        self.trading_price = 0
        self.order_id = "000000000000"
        self.uniqueOrderId = "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
        self.trade_details = {"success": False, "index": None, "datetime": datetime.now()}

    # this is our main strategy function
    def check_indicators(self, data: pd.DataFrame, passed_token: Token, ltp_value: float, index: int = 0):
        ltp = ltp_value

        token = str(passed_token).split(":")[-1]  # this is actually symbol written as FINNIFTY23JUL2423500CE
        symbol_token = str(passed_token).split(":")[
            1
        ]  # a five digit integer number to represent the actual token number for the symbol
        index_info = [token, symbol_token, ltp]
        try:
            # checking for pre buying condition
            if self.waiting_for_buy == True:

                current_candle = data.iloc[1]  # latest candle formed
                previous_candle = data.iloc[2]  # last second candle formed
                print("PREVIOUS?CURRENT", previous_candle, current_candle)

                for i in range(1, constant.TRACE_CANDLE + 1):
                    current_candle = data.iloc[i]
                    previous_candle = data.iloc[i + 1]

                    if current_candle[constant.CLOSE] >= previous_candle[constant.HIGH]:
                        high_values = [float(data.iloc[j][constant.HIGH]) for j in range(i, 1, -1)]
                        try:
                            max_high = max(high_values)
                        except:
                            max_high = current_candle[constant.HIGH]
                        self.price = max_high
                        self.trading_price = max_high
                        self.trade_details["index"] = token
                        break

                    elif (8 * (float(current_candle[constant.HIGH]) - float(current_candle[constant.HIGH]))) < (
                        float(previous_candle[constant.HIGH]) - float(previous_candle[constant.LOW])
                    ):
                        # No need to reassign current_candle and previous_candle here since it's already done above.
                        self.price = current_candle[constant.HIGH]
                        self.trading_price = current_candle[constant.HIGH]
                        self.trade_details["index"] = token
                        break

            # buying conditions
            if (not self.to_buy) and (token == self.trade_details["index"]):
                if ltp > (constant.BUYING_MULTIPLIER * self.price):
                    self.to_buy = True
                    self.waiting_to_modify = True
                    self.waiting_to_modify_or_sell = True

                    self.waiting_for_buy = False

                    self.price = ltp
                    self.trade_details["success"] = True
                    self.trade_details["index"] = token

                    self.trade_details["datetime"] = datetime.now()

                    write_logs(
                        "BOUGHT", token, self.price, "NILL", f"LTP > condition matched self.price {self.trading_price}"
                    )

                    return (Signal.BUY, self.price, index_info)
                return (Signal.WAITING_TO_BUY, self.price, index_info)

            # # modify stop loss conditions
            # elif self.to_buy and not self.to_modify and self.waiting_to_modify and self.trade_details["index"] == token:
            #     if ltp > (self.price*1.20):
            #         logger.info(f"Modifying the stop-loss, ltp is 20%greater than original price")
            #         self.price = ltp
            #         # modifying the stop loss
            #         return (Signal.MODIFY, self.price, index_info)
            #     elif (data.iloc[1]["Low"] * 0.98) > self.stop_loss_price:
            #         logger.info(f"Modifying the stoploss price, current-low {data.iloc[1]['Low']} vs stop-loss-price {self.stop_loss_price} ")
            #         self.price = self.stop_loss_price
            #         # modifying the stop loss
            #         return (Signal.MODIFY, self.price, index_info)
            #     else:
            #         return (Signal.WAITING_TO_MODIFY, self.price, index_info)

            # direct selling condition
            elif not self.waiting_for_buy:
                if (
                    self.to_buy
                    and self.waiting_to_modify_or_sell
                    and self.trade_details["index"] == token
                    and self.trade_details["success"] == True
                ):

                    # finding max of three
                    stoploss_1 = self.stop_loss_price
                    stoploss_2 = data.iloc[1]["Low"] * constant.SL_LOW_MULTIPLIER_1
                    stoploss_3 = min([data.iloc[1]["Low"], data.iloc[2]["Low"]]) * constant.SL_LOW_MULTIPLIER_2
                    stoploss_condition_1 = round(max([stoploss_1, stoploss_2, stoploss_3]), 2)

                    if ltp >= (constant.TRAIL_SL_1 * self.price):
                        self.stop_loss_price = max(
                            round((self.price * constant.MODITY_STOP_LOSS_1), 2), stoploss_condition_1
                        )
                        self.price = self.stop_loss_price
                        logger.info(f"Modifying the stop-loss 20% condition, New_SL={self.stop_loss_price}")
                        return (Signal.MODIFY, self.stop_loss_price, index_info)

                    elif ltp >= (constant.TRAIL_SL_2 * self.price):
                        self.stop_loss_price = max(
                            round((self.price * constant.MODITY_STOP_LOSS_1), 2), stoploss_condition_1
                        )
                        self.price = self.stop_loss_price
                        logger.info(f"Modifying the stop-loss 10% condition, New_SL={self.stop_loss_price}")
                        return (Signal.MODIFY, self.stop_loss_price, index_info)

                    elif stoploss_condition_1 > self.stop_loss_price:
                        self.stop_loss_price = stoploss_condition_1
                        self.price = self.stop_loss_price
                        logger.info(
                            f"Modifying the stop-loss according to Low condition, New_SL={self.stop_loss_price}"
                        )
                        return (Signal.MODIFY, self.stop_loss_price, index_info)

                    elif ltp <= self.stop_loss_price:
                        self.trade_details["success"] = False
                        self.trade_details["index"] = None
                        self.trade_details["datetime"] = datetime.now()

                        self.to_buy = False
                        self.waiting_to_modify_or_sell = False

                        self.to_sell = True
                        self.waiting_for_buy = True
                        return (Signal.SELL, ltp, index_info)
                    else:
                        self.waiting_to_modify_or_sell = True
                        return (Signal.WAITING_FOR_MODIFY_OR_SELL, self.stop_loss_price, index_info)
                else:
                    self.waiting_to_modify_or_sell = True
                    return (Signal.WAITING_FOR_MODIFY_OR_SELL, self.stop_loss_price, index_info)

            elif self.waiting_to_modify_or_sell:
                return (Signal.WAITING_FOR_MODIFY_OR_SELL, self.price, index_info)

            else:
                self.waiting_for_buy = True
                self.trade_details["success"] = False
                return (Signal.WAITING_TO_BUY, self.price, index_info)
        except Exception as exc:
            logger.error(f"An error occurred while checking indicators: {exc}")
            return (Signal.NULL, 0, [])


# to access objects of dataframe and dict kind
def async_return(result):
    obj = asyncio.Future()
    obj.set_result(result)
    return obj


class BaseStrategy:
    def __init__(
        self,
        instrument_reader: InstrumentReaderInterface,
        data_provider: DataProviderInterface,
        indicator: MultiIndexStrategy,
        index_candle_durations: Dict[str, str],
        extra_args: dict,
        extra_args_amount: dict,
        current_profit: float,
        target_profit: float,
        strategy_id: str
    ):
        self.instruments = instrument_reader.read_instruments()
        self.data_provider = data_provider
        self.indicator = indicator
        self.index_candle_durations = index_candle_durations
        self.ltp_comparison_interval = 2
        # self.index_candle_data: Dict[str, list] = {}
        self.index_ltp_values: Dict[str, float] = {}
        self.token_value: Dict[str, Token] = {}
        self.token: Token
        self.stop_event = asyncio.Event()
        self.parameters = extra_args
        self.parameters_amount = extra_args_amount
        self.lotsize: int
        self.trading_quantity: int
        self.buying_price: int
        self.current_profit: float = current_profit
        self.target_profit: float = target_profit
        self.token_id: str = ""
        self.strategy_id: str = strategy_id

    # data = {
    #         token: str,
    #         symbol: str,
    #         name: str,
    #         expiry: str,
    #         strike: float,
    #         lotsize: int,
    #         instrumenttype: str,
    #         exch_seg: str,
    #         tick_size: float,
    #  }

    async def fetch_ltp_data(self):
        try:
            for instrument in self.instruments:
                self.token = Token(instrument.exch_seg, instrument.token, instrument.symbol)
                self.token_value[str(instrument.symbol)] = self.token
                ltp_data = await async_return(self.data_provider.fetch_ltp_data(self.token))
                # if "data" not in ltp_data or "ltp" not in ltp_data["data"]:
                #     logger.error("No 'ltp' key in the LTP response JSON")
                #     continue  # Continue to the next instrument
                # self.index_ltp_values[str(instrument.symbol)] = float(ltp_data["data"]["ltp"])
                self.index_ltp_values[str(instrument.symbol)] = float(ltp_data)
                # logger.info(f"self.index_ltp_values: {self.index_ltp_values}")
        except Exception as e:
            logger.error(f"An error occurred while fetching LTP data: {e}")

    async def fetch_candle_data(self):
        try:
            for instrument in self.instruments:
                self.token = Token(instrument.exch_seg, instrument.token, instrument.symbol)
                candle_duration = self.index_candle_durations[instrument.symbol]
                candle_data = await async_return(
                    self.data_provider.fetch_candle_data(self.token, interval=candle_duration)
                )
                # candle_data = async_return(candle_data)
                if candle_data is None or len(candle_data) == 0:
                    logger.error(f"No candle data returned for {instrument.symbol}")
                    continue  # Continue to the next instrument
                # INDEX_CANDLE_DATA.update({str(instrument.symbol) : candle_data})
                # print(f"checking candle ======> {candle_data}")
                INDEX_CANDLE_DATA.append((str(instrument.symbol), candle_data))
        except logging.exception:
            logger.error(f"An error occurred while fetching candle data")

    async def process_data(self):
        print(f"calling process data")
        try:
            for index, value in INDEX_CANDLE_DATA:
                await asyncio.sleep(1)
                print("Inside try")
                if value and self.index_ltp_values[index]:
                    columns = ["timestamp", "Open", "High", "Low", "Close", "Volume"]
                    data = pd.DataFrame(value, columns=columns)

                    # if len(data) < 2:
                    #     logger.warning(f"Not enough candle data for {index}, only {len(data)} rows available")
                    #     continue

                    latest_candle = data.iloc[1]
                    print("latest candle", latest_candle)
                    # Implement your comparison logic here
                    print("Current profit", self.current_profit, self.target_profit)
                    if self.current_profit >= self.target_profit:
                        print("BREAKING HERE")
                        break

                    signal, price_returned, index_info = await async_return(
                        self.indicator.check_indicators(data, self.token_value[index], self.index_ltp_values[index],
                                                        self.strategy_id)
                    )

                    logger.info(
                        f"SIGNAL:{signal}, PRICE:{self.indicator.price}, INDEX:{index_info[0]}, LTP:{index_info[-1]}"
                    )

                    if signal == Signal.BUY:
                        # uncomment to start paper trading
                        # def save_trade(new_trade: TradeDetails):
                        #     global db
                        #     db.add(new_trade)
                        #     db.commit()
                        #     db.refresh(new_trade)
                        #     return new_trade

                        # def initialize_db():
                        #     global db
                        #     db = SessionLocal()

                        # initialize_db()

                        # self.indicator.price = self.indicator.price
                        # self.indicator.stop_loss_price = self.indicator.price * constant.STOP_LOSS_MULTIPLIER
                        # logger.info(
                        #     f"Trade BOUGHT at {self.indicator.price} in {index_info[0]} with SL={self.indicator.stop_loss_price}"
                        # )

                        for instrument in self.instruments:
                            if instrument.symbol == index:
                                self.token_id = instrument.token

                        if self.parameters_amount[index] == 0:
                            self.trading_quantity = self.parameters[index]

                        else:
                            for instrument in self.instruments:
                                if instrument.symbol == index:
                                    self.lotsize = int(instrument.lotsize)
                                    # self.token_id = instrument.token

                            amount = self.parameters_amount[index]
                            number_of_stocks = int(amount / (self.indicator.price * self.lotsize))
                            quantity = self.lotsize * number_of_stocks
                            self.trading_quantity = quantity
                            logger.info(f"Trade Quantity for {index} - {quantity}")

                        current_time = datetime.now()

                        # new_trade = TradeDetails(
                        #     user_id=1,
                        #     signal="BUY",
                        #     price=self.indicator.price,
                        #     trade_time=current_time,
                        #     token_id=self.token_id,
                        # )
                        # print(f"#############{saved_trade}###############")
                        # saved_trade = save_trade(new_trade)

                        self.indicator.order_id, trade_book_full_response = await async_return(
                            self.data_provider.place_order(
                                index_info[0],
                                index_info[1],
                                "BUY",
                                "LIMIT",
                                self.indicator.price,
                                self.trading_quantity,
                            )
                        )

                        # await place_order_mail(db)

                        # uncomment to start actual trading
                        self.indicator.order_id, trade_book_full_response = await async_return(
                            self.data_provider.place_order(index_info[0], index_info[1], "BUY", "MARKET",
                                                           price_returned, self.parameters[index]))
                        self.indicator.price = float(trade_book_full_response['fillprice'])
                        self.indicator.stop_loss_price = round(self.indicator.price * 0.95, 2)
                        logger.info(
                            f"Trade BOUGHT at {float(trade_book_full_response['fillprice'])} in {index_info[0]} with SL={self.indicator.stop_loss_price}")

                    elif signal == Signal.SELL:
                        # uncomment to start paper trading
                        # await place_order_mail()

                        for instrument in self.instruments:
                            if instrument.symbol == index:
                                self.token_id = instrument.token

                        # def save_trade(new_trade: TradeDetails):
                        #     global db
                        #     db.add(new_trade)
                        #     db.commit()
                        #     db.refresh(new_trade)
                        #     return new_trade

                        # def initialize_db():
                        #     global db
                        #     db = SessionLocal()

                        # initialize_db()

                        current_time = datetime.now()

                        # new_trade = TradeDetails(
                        #     user_id=1,
                        #     signal="SELL",
                        #     price=self.indicator.price,
                        #     trade_time=current_time,
                        #     token_id=self.token_id,
                        # )

                        # saved_trade = save_trade(new_trade)

                        # self.indicator.price, self.indicator.stop_loss_price = 0, 0
                        # logger.info(f"TRADE SOLD at {price_returned} in {index_info[0]}")

                        # uncomment to start actual trading
                        self.indicator.order_id, trade_book_full_response = await async_return(
                            self.data_provider.place_order(index_info[0], index_info[1], "SELL", "MARKET",
                                                           price_returned, self.parameters[index]))
                        self.indicator.price, self.indicator.stop_loss_price = 0, 0
                        logger.info(f"TRADE SOLD at {float(trade_book_full_response['fillprice'])} in {index_info[0]}")

                else:
                    logger.info("Waiting for data...")
        except Exception as e:
            logger.info(f"Error while calling process_data {str(e)}")
            raise

    async def start(self):
        try:
            while not self.stop_event.is_set():
                await self.fetch_candle_data()
                await asyncio.sleep(10)  # fetch candle data every 10 seconds
        except asyncio.CancelledError:
            logger.info("start task was cancelled")
            raise

    async def run(self):
        await asyncio.gather(self.fetch_ltp_data_continuous(), self.process_data_continuous(), self.start())

    async def fetch_ltp_data_continuous(self):
        try:
            while not self.stop_event.is_set():
                await self.fetch_ltp_data()
                await asyncio.sleep(1)  # fetch LTP data every second
        except asyncio.CancelledError:
            logger.info("fetch_ltp_data_continuous task was cancelled")
            raise

    async def process_data_continuous(self):
        try:
            while not self.stop_event.is_set():
                await self.process_data()
                await asyncio.sleep(1)  # fetch LTP data every second
        except asyncio.CancelledError:
            logger.info("process_data_continuous task was cancelled")
            raise

    async def stop(self):
        self.stop_event.set()


# def on_data(wsapp, msg):
#     """Handles incoming WebSocket data."""
#     try:
#         token = msg.get('token')
#         ltp = msg.get('last_traded_price', 0) / 100.0  # Convert to proper format
        
#         LIVE_FEED_JSON[token] = {
#             'token': token,
#             'ltp': ltp,
#             'exchange_timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
#         }
#         logger.info(f"Live Data Received: {LIVE_FEED_JSON}")
#     except Exception as e:
#         logger.error(f"Error in on_data: {e}")

def on_data(wsapp, msg):
    """Handles incoming WebSocket data."""
    try:
        # Check if msg is a string (sometimes WebSockets return string JSON)
        if isinstance(msg, str):
            try:
                msg = json.loads(msg)
            except JSONDecodeError:
                logger.error(f"Could not parse WebSocket string message: {msg}")
                return
                
        # Extract token and LTP
        token = msg.get('token')
        if not token:
            logger.warning(f"Received WebSocket message without token: {msg}")
            return
            
        # Convert LTP to proper format (some APIs return in paise/cents)
        ltp_raw = msg.get('last_traded_price', 0)
        # Decide if we need to divide by 100 based on value
        ltp = ltp_raw / 100.0 if ltp_raw > 10000 else ltp_raw  
        
        # Update global dictionary with latest data
        LIVE_FEED_JSON[token] = {
            'token': token,
            'ltp': ltp,
            'timestamp': datetime.now().isoformat(),
            'raw_data': msg  # Store raw data for debugging
        }
        
        # Log data receipt but not too frequently to avoid log bloat
        should_log = int(datetime.now().timestamp()) % 10 == 0  # Log once every 10 seconds
        if should_log:
            logger.info(f"WebSocket data received for token {token}, LTP: {ltp}")
            
    except Exception as e:
        logger.error(f"Error processing WebSocket data: {e}", exc_info=True)

def on_error(wsapp, error):
    """Handles WebSocket errors."""
    logger.error(f"WebSocket Error: {error}")

# def on_close(wsapp):
#     """Handles WebSocket disconnections."""
#     logger.info("WebSocket Connection Closed")
def on_close(wsapp, status, reason):
    """Handles WebSocket disconnections."""
    logger.info(f"WebSocket Connection Closed with status: {status}, reason: {reason}")
    # Perform any necessary cleanup or reconnection logic here, if needed
def close_connection(sws):
    """Closes WebSocket connection properly."""
    sws.max_retry_attempt = 0  # Stop retry attempts
    sws.close_connection()
    logger.info("WebSocket connection closed manually.")

def subscribe_symbol(token_list, sws):
    """Subscribes to a list of tokens."""
    logger.info(f"Subscribing to tokens: {token_list}")
    sws.subscribe(CORRELATION_ID, FEED_MODE, token_list)

def connectFeed(sws, token_list=None):
    """Establishes WebSocket connection and subscribes to tokens."""
    def on_open(wsapp):
        logger.info("WebSocket Connection Opened")
        if token_list:
            subscription_payload = [{"exchangeType": 2, "tokens": token_list}]
            # subscription_payload = [{"exchangeType": 2, "tokens": ["41734", "41735"]}, {"exchangeType" : 5, "tokens" : ["252453", "250060"]}]

            logger.info(f"Subscribing with payload: {subscription_payload}")
            try:
                sws.subscribe(CORRELATION_ID, FEED_MODE, subscription_payload)
            except Exception as e:
                logger.error(f"WebSocket Subscription Error: {e}")
        else:
            logger.warning("No tokens provided for subscription.")
    sws.on_open = on_open
    sws.on_data = on_data
    sws.on_error = on_error
    sws.on_close = on_close

    threading.Thread(target=sws.connect, daemon=True).start()

# @router.post("/start_strategy")
# async def start_strategy(strategy_params: StartStrategySchema):
#     try:
#         print("STRATEGY PARAMS", strategy_params)
#         current_profit = -1
#         target_profit = strategy_params.target_profit
#         strategy_id = strategy_params.strategy_id
#         index_and_candle_durations = {}
#         quantity_index = {}
#         amount_index = {}

#         for index in strategy_params.index_list:
#             key = f"{index.index}{index.expiry}{index.strike_price}{index.option}"
#             index_and_candle_durations[key] = index.chart_time
#             quantity_index[key] = index.quantity
#             amount_index[key] = index.trading_amount

#         if strategy_id in tasks:
#             raise HTTPException(status_code=400, detail="Strategy already running")


#         try:
#             smart.generateSession(clientCode=CLIENT_CODE, password=PASSWORD, totp=pyotp.TOTP(TOKEN_CODE).now())
#             ltp_smart.generateSession(
#                 clientCode=LTP_CLIENT_CODE, password=LTP_PASSWORD, totp=pyotp.TOTP(LTP_TOKEN_CODE).now()
#             )
#         except Exception as e:
#             return {"message": str(e), "success": True}

#         instrument_reader = OpenApiInstrumentReader(NFO_DATA_URL, list(index_and_candle_durations.keys()))
#         smart_api_provider = SmartApiDataProvider(smart, ltp_smart)
#         max_transactions_indicator = MultiIndexStrategy()

#         strategy = BaseStrategy(
#             instrument_reader,
#             smart_api_provider,
#             max_transactions_indicator,
#             index_and_candle_durations,
#             quantity_index,
#             amount_index,
#             current_profit,
#             target_profit,
#             strategy_id,
#         )
#         strategy.ltp_comparison_interval = 5

#         task = asyncio.create_task(strategy.run(), name=strategy_id)
#         tasks[strategy_id] = task

#         response = {"message": "strategy starts", "success": True, "strategy_id": strategy_id}
#         logger.info("Response", response)
#         return response

#     except Exception as exc:
#         logger.info("Error in running strategy", exc_info=True)
#         response = {
#             "message": f"Strategy failed to start: {exc}",
#             "success": False,
#         }
#         return response

@router.post("/start_strategy")
async def start_strategy(strategy_params: StartStrategySchema):
    try:
        print("STRATEGY PARAMS", strategy_params)
        current_profit = -1
        target_profit = strategy_params.target_profit
        strategy_id = strategy_params.strategy_id
        index_and_candle_durations = {}
        quantity_index = {}
        amount_index = {}

        for index in strategy_params.index_list:
            key = f"{index.index}{index.expiry}{index.strike_price}{index.option}"
            index_and_candle_durations[key] = index.chart_time
            quantity_index[key] = index.quantity
            amount_index[key] = index.trading_amount

        if strategy_id in tasks:
            raise HTTPException(status_code=400, detail="Strategy already running")

        try:
            # Generate session tokens
            session_response = smart.generateSession(clientCode=CLIENT_CODE, password=PASSWORD, totp=pyotp.TOTP(TOKEN_CODE).now())
            ltp_smart.generateSession(
                clientCode=LTP_CLIENT_CODE, password=LTP_PASSWORD, totp=pyotp.TOTP(LTP_TOKEN_CODE).now()
            )
            
            # Get tokens from session for WebSocket
            feed_token = session_response['data']['feedToken']
            auth_token = session_response['data']['jwtToken']
            
        except Exception as e:
            return {"message": f"Authentication failed: {str(e)}", "success": False}

        # Set up instrument reader with the selected instruments
        instrument_reader = OpenApiInstrumentReader(NFO_DATA_URL, list(index_and_candle_durations.keys()))
        print("Symbols being used:", list(index_and_candle_durations.keys()))  # Debugging line

        instruments = instrument_reader.read_instruments()
        print("Instrument Reader Object:", instrument_reader)  # Debugging line
        print("Instruments Retrieved:", instruments)
        # Collect tokens for WebSocket subscription
        tokens_to_subscribe = []
        for instr in instruments:
            try:
                token_int = int(instr.token)
                tokens_to_subscribe.append(token_int)
            except Exception as e:
                logger.error(f"Error converting token {instr.token} to int: {e}")
                
        if not tokens_to_subscribe:
            return {"message": "No valid instrument tokens found", "success": False}
            
        logger.info(f"Setting up WebSocket with tokens: {tokens_to_subscribe}")
        
        # Initialize and connect WebSocket
        sws = SmartWebSocketV2(auth_token, API_KEY, CLIENT_CODE, feed_token, max_retry_attempt=5)
        connectFeed(sws, tokens_to_subscribe)
        
        # Store WebSocket connection for cleanup later
        websocket_connections[strategy_id] = sws
        
        # Clear existing data for these tokens
        for token in tokens_to_subscribe:
            if str(token) in LIVE_FEED_JSON:
                del LIVE_FEED_JSON[str(token)]
        
        # Initialize a modified version of SmartApiDataProvider that uses WebSocket data
        smart_api_provider = WebSocketEnabledDataProvider(smart, ltp_smart, LIVE_FEED_JSON)
        max_transactions_indicator = MultiIndexStrategy()

        strategy = BaseStrategy(
            instrument_reader,
            smart_api_provider,
            max_transactions_indicator,
            index_and_candle_durations,
            quantity_index,
            amount_index,
            current_profit,
            target_profit,
            strategy_id,
        )
        
        # Increase interval to avoid rate limiting
        strategy.ltp_comparison_interval = 5

        task = asyncio.create_task(strategy.run(), name=strategy_id)
        tasks[strategy_id] = task

        response = {
            "message": "Strategy started with WebSocket integration",
            "success": True,
            "strategy_id": strategy_id,
            "websocket_status": "connected"
        }
        logger.info(f"Strategy started: {response}")
        return response

    except Exception as exc:
        logger.error(f"Error in running strategy: {exc}", exc_info=True)
        
        # Cleanup any WebSocket if it was created
        if 'strategy_id' in locals() and strategy_id in websocket_connections:
            try:
                close_connection(websocket_connections[strategy_id])
                del websocket_connections[strategy_id]
            except Exception:
                pass
                
        response = {
            "message": f"Strategy failed to start: {str(exc)}",
            "success": False,
        }
        return response

# Stop strategy endpoint
# @router.get("/stop_strategy/{strategy_id}")
# async def stop_strategy(strategy_id):
#     try:
#         if strategy_id not in tasks:
#             raise HTTPException(status_code=400, detail="Strategy not found")
#         task_info = tasks[strategy_id]
#         task_info.cancel()
#         await task_info
#     except asyncio.CancelledError:
#         del tasks[strategy_id]
#         raise HTTPException(status_code=200, detail="Strategy Stop")

#     del tasks[strategy_id]
#     return {"message": "Strategy stopped", "success": True}


# Create a dictionary to track WebSocket connections

websocket_connections = {}

# @router.get("/stop_strategy/{strategy_id}")
# async def stop_strategy(strategy_id):
#     try:
#         if strategy_id not in tasks:
#             raise HTTPException(status_code=400, detail="Strategy not found")
        
#         # Cancel the strategy task
#         task_info = tasks[strategy_id]
#         task_info.cancel()
#         await task_info
        
#         # Close WebSocket connection if it exists
#         if strategy_id in websocket_connections:
#             try:
#                 sws = websocket_connections[strategy_id]
#                 close_connection(sws)
#                 del websocket_connections[strategy_id]
#                 logger.info(f"WebSocket connection closed for strategy {strategy_id}")
#             except Exception as e:
#                 logger.error(f"Error closing WebSocket for strategy {strategy_id}: {e}")
        
#     except asyncio.CancelledError:
#         if strategy_id in tasks:
#             del tasks[strategy_id]
#         raise HTTPException(status_code=200, detail="Strategy stopped")

#     # Clean up
#     if strategy_id in tasks:
#         del tasks[strategy_id]
    
#     return {"message": "Strategy and WebSocket connections stopped", "success": True}


@router.get("/stop_strategy/{strategy_id}")
async def stop_strategy(strategy_id: str):
    try:
        # Check if the strategy_id exists in tasks
        if strategy_id not in tasks:
            logger.error(f"Strategy {strategy_id} not found in tasks.")
            raise HTTPException(status_code=400, detail="Strategy not found")
        
        # Retrieve the task to be canceled
        task_info = tasks[strategy_id]
        logger.info(f"Cancelling task for strategy {strategy_id}.")
        task_info.cancel()

        # Ensure the task is fully cancelled
        if not task_info.done():
            try:
                await task_info  # Safe to await, ensures cancellation is processed
            except asyncio.CancelledError:
                logger.info(f"Task {strategy_id} successfully cancelled.")
            except Exception as e:
                logger.error(f"Error awaiting cancellation of task {strategy_id}: {e}")
                raise HTTPException(status_code=500, detail="Error awaiting cancellation")

        # Close WebSocket connection if it exists
        if strategy_id in websocket_connections:
            try:
                sws = websocket_connections[strategy_id]
                logger.info(f"Closing WebSocket for strategy {strategy_id}.")
                close_connection(sws)  # Ensure this function is working properly
                del websocket_connections[strategy_id]
                logger.info(f"WebSocket connection closed for strategy {strategy_id}")
            except Exception as e:
                logger.error(f"Error closing WebSocket for strategy {strategy_id}: {e}")
                raise HTTPException(status_code=500, detail="Error closing WebSocket")

        # Ensure task is removed after cancellation and WebSocket closure
        if strategy_id in tasks:
            logger.info(f"Removing task entry for strategy {strategy_id}.")
            del tasks[strategy_id]
    
        logger.info(f"Strategy {strategy_id} and WebSocket connections stopped successfully.")
        return {"message": "Strategy and WebSocket connections stopped", "success": True}

    except Exception as e:
        logger.error(f"Error stopping strategy {strategy_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")





@router.post("/live_strategy_data")
async def live_strategy_data(strategy_params: StartStrategySchema):
    try:
        # Build a composite key for each index and prepare candle durations if needed
        index_and_candle_durations = {}
        for index in strategy_params.index_list:
            key = f"{index.index}{index.expiry}{index.strike_price}{index.option}"
            index_and_candle_durations[key] = index.chart_time

        # Use the composite keys as token list since the index objects do not have a token attribute.
        token_list = list(index_and_candle_durations.keys())
        print(token_list, "token_list")
        # Generate session tokens for WebSocket subscription
        session_response = smart.generateSession(
            clientCode=CLIENT_CODE,
            password=PASSWORD,
            totp=pyotp.TOTP(TOKEN_CODE).now()
        )
        ltp_smart.generateSession(
            clientCode=LTP_CLIENT_CODE,
            password=LTP_PASSWORD,
            totp=pyotp.TOTP(LTP_TOKEN_CODE).now()
        )
        feed_token = session_response['data']['feedToken']
        auth_token = session_response['data']['jwtToken']

        # Create instrument reader with the keys from index_list
        instrument_reader = OpenApiInstrumentReader(NFO_DATA_URL, list(index_and_candle_durations.keys()))
        instruments = instrument_reader.read_instruments()
        if not instruments:
            return {"message": "No instruments found", "success": False}

        # Collect tokens from instruments for WebSocket subscription
        tokens_to_subscribe = []
        for instr in instruments:
            try:
                token_int = int(instr.token)
                tokens_to_subscribe.append(token_int)
            except Exception as e:
                logger.error(f"Error converting token {instr.token} to int: {e}")

        if not tokens_to_subscribe:
            return {"message": "No valid instrument tokens found", "success": False}

        logger.info(f"Final Tokens to Subscribe: {tokens_to_subscribe}")
        print(tokens_to_subscribe, "tokens_to_subscribe")
        # Initialize and connect WebSocket with the token list
        sws = SmartWebSocketV2(auth_token, API_KEY, CLIENT_CODE, feed_token, max_retry_attempt=5)
        connectFeed(sws, tokens_to_subscribe)

        # Optionally, wait a moment to let some data come in (adjust as necessary)
        await asyncio.sleep(2)

        # Return the live data captured by the WebSocket callbacks
        return {
            "message": "Live strategy data fetched from WebSocket successfully",
            "data": LIVE_FEED_JSON,
            "success": True
        }

    except Exception as e:
        logger.error(f"Error in live_strategy_data API: {e}", exc_info=True)
        return {"message": f"Error in live_strategy_data API: {e}", "success": False}


# get all trades with strik prices
@router.get("/get-margin-calculator")
def get_all_strike_prices():
    response = requests.get(NFO_DATA_URL)
    response.raise_for_status()
    data = response.json()
    with open("data.json", "w") as json_file:
        json.dump(data, json_file, indent=4)
    return {"message": "all strike list", "success": True}

class WebSocketEnabledDataProvider(SmartApiDataProvider):
    def __init__(self, smart: SmartConnect, ltpSmart: SmartConnect, live_feed_data: dict):
        super().__init__(smart, ltpSmart)
        self.__smart = smart
        self.__ltpSmart = ltpSmart
        self.__live_feed_data = live_feed_data
        
    def fetch_ltp_data(self, token):
        try:
            # First try to get data from WebSocket feed
            token_id = token.token_id
            if token_id in self.__live_feed_data and 'ltp' in self.__live_feed_data[token_id]:
                ltp = self.__live_feed_data[token_id]['ltp']
                logger.info(f"Using WebSocket LTP data for {token.symbol}: {ltp}")
                return ltp
                
            # Fall back to API call if WebSocket data not available
            logger.info(f"WebSocket data not available for {token.symbol}, using API")
            ltp_data = self.__ltpSmart.ltpData("NFO", token.symbol, token.token_id)
            
            # Add a small delay to avoid rate limiting
            sleep(0.5)
            
            if not ltp_data or 'data' not in ltp_data or 'ltp' not in ltp_data['data']:
                raise ValueError(f"Invalid LTP data returned for {token.symbol}")
                
            return ltp_data['data']['ltp']
        except Exception as e:
            logger.error(f"LTP data exception: {e}")
            raise ValueError(f"Failed to fetch LTP data: {e}")
            