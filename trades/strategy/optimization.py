import asyncio
import copy
import json
import logging
import os
from datetime import datetime, timedelta
from enum import Enum
from json.decoder import JSONDecodeError
from time import sleep
from typing import Dict, List, Tuple
from urllib.error import URLError
#from curd import save_trade
import fastapi
import pandas as pd
import pyotp
import requests
from dotenv import load_dotenv
from fastapi import HTTPException
from SmartApi import SmartConnect
from trades.models import TradeDetails
from trades.schema import StartStrategySchema
from trades.strategy.utility import place_order_mail, save_order, save_strategy
from config.database.config import SessionLocal

router = fastapi.APIRouter()
tasks: Dict[str, asyncio.Task] = {}

load_dotenv()
# api_key = os.getenv("API_KEY")
# client_code = os.getenv("CLIENT_CODE")
# password = os.getenv("PASSWORD")
# token_code = os.getenv("TOKEN_CODE")


db = None

class Constants:
    def __init__(self):
        self.API_KEY = "T4MHVpXH"
        self.CLIENT_CODE = "J263557"
        self.PASSWORD = "7753"
        self.TOKEN_CODE = "3MYXRWJIJ2CZT6Y5PD2EU5RNNQ"
        self.NFO_DATA_URL = "https://margincalculator.angelbroking.com/OpenAPI_File/files/OpenAPIScripMaster.json"
        self.OPT_TYPE = "OPTIDX"
        self.INDEX_CANDLE_DATA = []
        self.EXCH_TYPE = "NFO"
        self.LTP_API_KEY = "MolOSZTR"
        self.LTP_CLIENT_CODE = "S55329579"
        self.LTP_PASSWORD = "4242"
        self.LTP_TOKEN_CODE = "QRLYAZPZ6LMTH5AYILGTWWN26E"

        self.TRACE_CANDLE = 5
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

# client code to get LTP data
LTP_API_KEY = "MolOSZTR"
LTP_CLIENT_CODE = "S55329579"
LTP_PASSWORD = "4242"
LTP_TOKEN_CODE = "QRLYAZPZ6LMTH5AYILGTWWN26E"


api_key = "T4MHVpXH"
client_code = "J263557"
password = "7753"
token_code = "3MYXRWJIJ2CZT6Y5PD2EU5RNNQ"

# index details
NFO_DATA_URL = "https://margincalculator.angelbroking.com/OpenAPI_File/files/OpenAPIScripMaster.json"
OPT_TYPE = "OPTIDX"
EXCH_TYPE = "NFO"

# client code to get LTP data
LTP_API_KEY = "MolOSZTR"
LTP_CLIENT_CODE = "S55329579"
LTP_PASSWORD = "4242"
LTP_TOKEN_CODE = "QRLYAZPZ6LMTH5AYILGTWWN26E"

# https://pypi.org/project/smartapi-python/
# objects to get `@smart` candle data and `@ltp_smart`LTP data respectively
smart = SmartConnect(api_key=api_key)
ltp_smart = SmartConnect(api_key=LTP_API_KEY)


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def write_logs(type, index, price, status, reason):
    log_dir = f"logs/trade/{datetime.today().strftime('%Y-%m-%d')}"
    datetime.today()
    log_file = os.path.join(log_dir, "logs.txt")

    # Create the directory if it does not exist
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # Open the file and append the log
    with open(log_file, "a+") as f:
        f.write(f"Trade {type} in {index} at {price} with {status}, reason {reason} at {datetime.now()} \n")

    print("LOGS WRITTEN")


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
            # Robust error handling to ensure proper data reading
            response = requests.get(self.url)
            response.raise_for_status()
            data = response.json()

            with open("data.json", "w") as json_file:
                json.dump(data, json_file, indent=4)
            return [Instrument(**item) for item in data if item["exch_seg"] == "NFO" and item["symbol"] in self.tokens]
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
        to_date = datetime.now()
        from_date = to_date - timedelta(minutes=360)
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
        data = res_json["data"][::-1]
        return data[:15]

    def fetch_ltp_data(self, token):
        ltp_data = self.__ltpSmart.ltpData("NFO", token.symbol, token.token_id)
        return ltp_data

    def get_trade_book(self, order_id):
        sleep(2)
        while True:
            try:
                order_book = self.__smart.tradeBook()["data"]
                for i in order_book:
                    if i["orderid"] == order_id:
                        return order_id, i
            except Exception as e:
                sleep(5)
                logger.info(f"Could not fetch the trade_book: {str(e)}")

    def get_order_book(self, order_id):
        sleep(2)
        while True:
            try:
                order_book = self.__smart.orderBook()["data"]
                for i in order_book:
                    if i["orderid"] == order_id:
                        return order_id, i
            except Exception as e:
                sleep(5)
                logger.info(f"Could not fetch the order_book: {str(e)}")

    def place_order(self, symbol, token, transaction, ordertype, price, quantity):
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
            # order_id = self.__smart.placeOrder(orderparams)
            # sleep(1)
            # logger.info(f"PlaceOrder id : {order_id} ")
            # order_id, i = self.get_trade_book(order_id=order_id)
            # return order_id, i
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
            # order_id = self.__smart.placeOrder(stoploss_limit_order_params)
            # logger.info(f"STOPLOSS ID: {order_id}")
            # sleep(1)
            # order_id, i = self.get_trade_book(order_id=order_id)
            # return order_id, i
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


# main class of strategy
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
        target_profit: float
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
        self.current_profit: int = current_profit
        self.target_profit: int = target_profit
        self.token_id : str = ''

        
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
                if "data" not in ltp_data or "ltp" not in ltp_data["data"]:
                    logger.error("No 'ltp' key in the LTP response JSON")
                    continue  # Continue to the next instrument
                self.index_ltp_values[str(instrument.symbol)] = float(ltp_data["data"]["ltp"])
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
                if candle_data is None:
                    logger.error(f"No candle data returned for {instrument.symbol}")
                    continue  # Continue to the next instrument
                constant.INDEX_CANDLE_DATA.append((str(instrument.symbol), candle_data))
        except logging.exception:
            logger.error(f"An error occurred while fetching candle data")

    async def process_data(self):
        print("calling process data")
        try:
            for index, value in constant.INDEX_CANDLE_DATA:
                await asyncio.sleep(1)
                if (value and self.index_ltp_values[index]) is not None:
                    columns = ["timestamp", "Open", "High", "Low", "Close", "Volume"]
                    data = pd.DataFrame(value, columns=columns)
                    latest_candle = data.iloc[1]

                    # Implement your comparison logic here
                    if self.current_profit >= self.target_profit:
                        break

                    signal, self.indicator.price, index_info = await async_return(
                        self.indicator.check_indicators(data, self.token_value[index], self.index_ltp_values[index])
                    )
                    logger.info(f"SIGNAL:{signal}, PRICE:{self.indicator.price}, INDEX:{index_info[0]}, LTP:{index_info[-1]}")

                    
                else:
                    print("else value")
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


# Start strategy endpoint
@router.post("/start_strategy")
async def start_strategy(strategy_params: StartStrategySchema):
    try:
        current_profit = 0.0
        target_profit = strategy_params.target_profit
        strategy_id = strategy_params.strategy_id
        index_and_candle_durations = {}
        quantity_index = {}
        amount_index = {}
        for index in strategy_params.index_list:
            index_and_candle_durations[f"{index.index}{index.expiry}{index.strike_price}{index.option}"] = (
                index.chart_time
            )

        for index in strategy_params.index_list:
            quantity_index[f"{index.index}{index.expiry}{index.strike_price}{index.option}"] = index.quantity

        for index in strategy_params.index_list:
            amount_index[f"{index.index}{index.expiry}{index.strike_price}{index.option}"] = index.trading_amount

        if strategy_params.strategy_id in tasks:
            raise HTTPException(status_code=400, detail="Strategy already running")

        ltp_smart.generateSession(
            clientCode=LTP_CLIENT_CODE, password=LTP_PASSWORD, totp=pyotp.TOTP(LTP_TOKEN_CODE).now()
        )

        try:
            smart.generateSession(clientCode=client_code, password=password, totp=pyotp.TOTP(token_code).now())
        except Exception as e:
            return {"message": str(e), "success": True}

        instrument_reader = OpenApiInstrumentReader(NFO_DATA_URL, list(index_and_candle_durations.keys()))
        smart_api_provider = SmartApiDataProvider(smart, ltp_smart)
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
        )
        task = asyncio.create_task(strategy.run(), name=strategy_id)
        # await save_strategy(strategy_params)
        tasks[strategy_id] = task
        response = {"message": "strategy starts", "success": True, "strategy_id": strategy_id}
        logger.info("Response", response)
        return response
    except Exception as exc:
        logger.info(f"Error in running strategy", exc)
        response = {
            "message": f"strategy failed to start, {exc}, ",
            "success": False,
        }
        return response


# Stop strategy endpoint
@router.get("/stop_strategy/{strategy_id}")
async def stop_strategy(strategy_id):
    try:
        if strategy_id not in tasks:
            raise HTTPException(status_code=400, detail="Strategy not found")
        task_info = tasks[strategy_id]
        task_info.cancel()
        await task_info
    except asyncio.CancelledError:
        del tasks[strategy_id]
        raise HTTPException(status_code=200, detail="Strategy Stop")

    del tasks[strategy_id]
    return {"message": "Strategy stopped", "success": True}


# get all trades with strik prices
@router.get("/get-margin-calculator")
def get_all_strike_prices():
    response = requests.get(NFO_DATA_URL)
    response.raise_for_status()
    data = response.json()
    with open("data.json", "w") as json_file:
        json.dump(data, json_file, indent=4)
    return {"message": "all strike list", "success": True}
