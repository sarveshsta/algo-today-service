import asyncio
import json
import logging
import os
from datetime import datetime, timedelta
from enum import Enum
from json.decoder import JSONDecodeError
from typing import Dict, List
from urllib.error import URLError

import fastapi
import pandas as pd
import pyotp
import requests
from dotenv import load_dotenv
from fastapi import HTTPException
from SmartApi import SmartConnect

from trades.schema import StartStrategySchema
from trades.strategy.utility import place_order_mail, save_order, save_strategy

router = fastapi.APIRouter()
tasks: Dict[str, asyncio.Task] = {}

load_dotenv()
api_key = os.getenv("API_KEY")
client_code = os.getenv("CLIENT_CODE")
password = os.getenv("PASSWORD")
token_code = os.getenv("TOKEN_CODE")


# constant data
global_order_id = 1111
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


# price comparision
OHLC_1 = "Close"
OHLC_2 = "High"

# buying condition comparision
buying_multiplier = 1.01
buying_OHLC = "High"

# selling condition comparision
trail_ltp_multiplier = 1.12
price_vs_ltp_mulitplier = 0.95

# stop loss condition
selling_OHLC1 = "High"
selling_OHLC1_multiplier = 1.10

selling_OHLC2 = "Low"
selling_OHLC2_multiplier = 0.95
# variables initialisation complete


class Signal(Enum):
    BUY = 1
    SELL = 2
    WAITING_TO_BUY = 3
    WAITING_TO_SELL = 4
    STOPLOSS = 5

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
    def fetch_candle_data(self, token: Token, interval: str = "ONE_MINUTE", symvol: str = "") -> pd.DataFrame:
        raise NotImplementedError("Subclasses must implement fetch_candle_data()")

    def fetch_ltp_data(self, token: Token, interval: str = "ONE_MINUTE", symvol: str = "") -> pd.DataFrame:
        raise NotImplementedError("Subclasses must implement fetch_ltp_data()")

    def place_order(self, symbol: str, token: str, transaction: str, ordertype: str, price: str, quantity:str):
        raise NotImplementedError("Subclasses must implement place_order()")

    def modify_stoploss_limit_order(self, symbol:str, token: str, quantity: str, stoploss_price: str, limit_price: str, order_id: str) -> pd.DataFrame:
        raise NotImplementedError("Subclasses must implement modify_order()")

    def place_stoploss_limit_order(self, symbol, token, quantity, stoploss_price, limit_price):
        raise NotImplementedError("Subclasses must implement modify_order()")


class SmartApiDataProvider(DataProviderInterface):
    def __init__(self, smart: SmartConnect, ltpSmart: SmartConnect):
        self.__smart = smart
        self.__ltpSmart = ltpSmart

    def fetch_candle_data(self, token, interval) -> pd.DataFrame:
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
        columns = ["timestamp", "Open", "High", "Low", "Close", "Volume"]
        df = pd.DataFrame(res_json["data"], columns=columns)
        data = df[::-1]
        return data

    def fetch_ltp_data(self, token):
        ltp_data = self.__ltpSmart.ltpData("NFO", token.symbol, token.token_id)
        return ltp_data

    def place_order(self, symbol, token, transaction, ordertype, price, quantity):
        if ordertype == "MARKET": price="0"
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
            logger.info(f"PlaceOrder id : {order_id}")

            # Method 2: Place an order and return the full response
            order_book = self.__smart.orderBook()['data']
            for i in order_book:
                if i['orderid'] == order_id:
                    return order_id, i
            return order_id, None
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
            except ValueError:
                raise ValueError("Stop-loss price and limit price must be numbers")

            stoploss_limit_order_params = {
                "variety": "STOPLOSS",
                "orderid": order_id,
                "tradingsymbol": symbol,
                "symboltoken": token,
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
            order_id = self.__smart.modifyOrder(stoploss_limit_order_params)
            logger.info(f"Modify id : {order_id}")

            # Method 2: Place an order and return the full response
            order_book = self.__smart.orderBook()['data']
            for i in order_book:
                if i['orderid'] == order_id:
                    return order_id, i
            return order_id, None
        except Exception as e:
            logger.info(f"Order modification failed: {e}")
            raise ValueError(f"Stop-loss modification failed, reason: {e}")

    def place_stoploss_limit_order(self, symbol, token, quantity, stoploss_price, limit_price):
        stoploss_price = round(stoploss_price, 1)
        limit_price = round(limit_price, 1)
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
            except ValueError:
                raise ValueError("Stop-loss price and limit price must be numbers")

            # Define stop-loss limit order parameters
            stoploss_limit_order_params = {
                "variety": "STOPLOSS",
                "tradingsymbol": symbol,
                "symboltoken": token,
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
            logger.info(f"ORDER STOPLOSS id : {order_id}")

            # Method 2: Place an order and return the full response
            order_book = self.__smart.orderBook()['data']
            for i in order_book:
                if i['orderid'] == order_id:
                    return order_id, i
            return order_id, None
        except Exception as e:
            logger.info(f"Stop loss Order place failed: {e}")
            raise ValueError(f"Stop-loss order failed, reason: {e}")


class IndicatorInterface:
    def check_indicators(self, data: pd.DataFrame) -> List[str]:
        raise NotImplementedError("Subclasses must implement check_indicators()")


# main class of strategy
class MaxMinOfLastTwo(IndicatorInterface):
    to_buy = False
    to_sell = False
    waiting_for_sell = False
    waiting_for_buy = True
    stop_loss = False
    price = 0
    trading_price = 0
    number_of_candles = 5
    stop_loss_info = None
    trade_details = {"done": False, "index": None, "datetime": datetime.now()}

    # this is our main strategy function
    def check_indicators(
        self, data: pd.DataFrame, passed_token: str, ltp_value: float, index: int = 0
    ) -> tuple[Signal, float]:
        print("TOKENN", passed_token)
        ltp = ltp_value

        token = str(passed_token).split(":")[-1] #this is actually symbol written as FINNIFTY23JUL2423500CE
        symbol_token = str(passed_token).split(":")[1] #a five digit integer number to represent the actual token number for the symbol
        index_info = [token, symbol_token]
        try:
            # checking for pre buying condition
            if self.waiting_for_buy == True:
                if self.number_of_candles > len(data) - 2:
                    self.number_of_candles = len(data) - 2

                for i in range(1, self.number_of_candles + 1):
                    logger.info("Looking for pivot value")
                    current_candle = data.iloc[i]
                    previous_candle = data.iloc[i + 1]

                    if current_candle[OHLC_1] >= previous_candle[OHLC_2]:
                        high_values = [float(data.iloc[j][OHLC_2]) for j in range(i, 0, -1)]
                        max_high = max(high_values)
                        logger.info(f"HIGH VALUES {high_values}")

                        self.price = max_high #pivot value
                        self.trading_price = max_high
                        self.trade_details["index"] = token

                        logger.info(f"Condition matched  {self.price}")
                        break

                    # elif (8 * (current_candle['High']-current_candle['Close'])) < (current_candle[i]["High"]- current_candle["Low"]):
                    #     current_candle = data.iloc[i]
                    #     previous_candle = data.iloc[i + 1]

                    #     self.price = data.iloc[i]["High"]
                    #     self.trading_price = data.iloc[i]["High"]
                    #     self.trade_details["index"] = token
                    #     logger.info(f"Condition matched when candle length compared")
                    #     logger.info(f"Pivot Value {self.price}")
                    #     break

            # buying conditions
            if not self.to_buy and token == self.trade_details["index"]:
                if ltp > (1.01 * self.price):
                    self.to_buy = True
                    self.waiting_for_sell = True

                    self.to_sell = False
                    self.waiting_for_buy = False
                    self.price = ltp
                    self.trade_details["done"] = True
                    self.trade_details["index"] = token

                    self.trade_details["datetime"] = datetime.now()
                    logger.info(f"TRADE BOUGHT due to LTP > Price {self.trade_details}")

                    write_logs(
                        "BOUGHT", token, self.price, "NILL", f"LTP > condition matched self.price {self.trading_price}"
                    )

                    stoploss_1 = (0.95 * self.price)
                    stoploss_2 = data.iloc[1]["Low"] * 0.97 
                    stoploss_3 = min([data.iloc[1]['Low'], data.iloc[2]['Low']]) * 0.99
                    logger.info(f"STOPLOSS Prices {stoploss_1} { stoploss_2} {stoploss_3}")
                    final_stoploss = max([stoploss_1, stoploss_2, stoploss_3])
                    self.price = round(final_stoploss, 1)  

                    return Signal.BUY, self.price, index_info
                return Signal.WAITING_TO_BUY, self.price, index_info

            # selling in profit
            elif self.to_buy and not self.to_sell and self.waiting_for_sell and self.trade_details["index"] == token:
                if ltp >= 1.10 * self.price:
                    self.to_sell = True
                    self.waiting_for_buy = True

                    self.to_buy = False
                    self.waiting_for_sell = False

                    write_logs(
                        "SOLD", token, self.price, "Profit", f"LTP > 1.10* buying self.price -> {ltp} > {self.price}"
                    )

                    self.price = ltp
                    self.trade_details["datetime"] = datetime.now()
                    self.trade_details["index"] = None
                    logger.info(f"TRADE SOLD PROFIT LTP {self.trade_details}")
                    return Signal.SELL, self.price, index_info

                stoploss_1 = (0.95 * self.price)
                stoploss_2 = data.iloc[1]["Low"] * 0.97 
                stoploss_3 = min([data.iloc[1]['Low'], data.iloc[2]['Low']]) * 0.99
                logger.info(f"STOPLOSS Prices {stoploss_1} { stoploss_2} {stoploss_3}")
                
                final_stoploss = max([stoploss_1, stoploss_2, stoploss_3])

                if final_stoploss < self.price:
                    # self.to_sell = True
                    self.stop_loss = True
                    self.waiting_for_buy = True

                    self.to_buy = False
                    self.waiting_for_sell = False

                    write_logs(
                        "ADDED Stop-Loss", token, self.price, "StopLoss", f"LTP < 0.95* buying self.price -> {ltp} > {self.price}"
                    )
                    self.trade_details["datetime"] = datetime.now()
                    self.trade_details["index"] = None
                    logger.info(f"ADDED STOP LOSS {self.trade_details}")
                    return Signal.STOPLOSS, self.price, index_info

            elif not self.to_sell and self.to_buy and not self.waiting_for_buy:
                self.waiting_for_sell = True
                logger.info(f"TRADE DETAILS {self.trade_details}")
                return Signal.WAITING_TO_SELL, self.price, index_info

            else:
                self.waiting_for_buy = True
                self.trade_details["done"] = False
                logger.info(f"TRADE DETAILS {self.trade_details}")
                return Signal.WAITING_TO_BUY, self.price, index_info
        except Exception as exc:
            logger.error(f"An error occurred while checking indicators: {exc}")
            return None, None, None

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
        indicator: IndicatorInterface,
        index_candle_durations: Dict[str, str],
    ):
        self.instruments = instrument_reader.read_instruments()
        self.data_provider = data_provider
        self.indicator = indicator
        self.index_candle_durations = index_candle_durations
        self.ltp_comparison_interval = 2
        self.candle_data = pd.DataFrame(columns=["timestamp", "Open", "High", "Low", "Close", "Volume"])
        self.ltp_value = None
        self.token = Token
        self.stop_event = asyncio.Event()

    async def fetch_ltp_data(self):
        try:
            for instrument in self.instruments:
                self.token = Token(instrument.exch_seg, instrument.token, instrument.symbol)
                ltp_data = await async_return(self.data_provider.fetch_ltp_data(self.token))
                if "data" not in ltp_data or "ltp" not in ltp_data["data"]:
                    logger.error("No 'ltp' key in the LTP response JSON")
                    continue  # Continue to the next instrument
                self.ltp_value = float(ltp_data["data"]["ltp"])
                logger.info(f"LTP Data Updated: {self.ltp_value}")
        except Exception as e:
            logger.error(f"An error occurred while fetching LTP data: {e}")

    async def fetch_candle_data(self):
        try:
            for instrument in self.instruments:
                self.token = Token(instrument.exch_seg, instrument.token, instrument.symbol)
                candle_duration = self.index_candle_durations[instrument.symbol]
                print("candle_duration: ",candle_duration)
                candle_data = await async_return(self.data_provider.fetch_candle_data(self.token, interval=candle_duration))
                if candle_data.empty:
                    logger.error(f"No candle data returned for {instrument.symbol}")
                    continue  # Continue to the next instrument
                self.candle_data = candle_data
        except Exception as e:
            logger.error(f"An error occurred while fetching candle data: {e}")

    async def process_data(self):
        while True:
            await asyncio.sleep(1)
            if not self.candle_data.empty and self.ltp_value is not None:
                latest_candle = self.candle_data.iloc[1]
                logger.info(f"Comparing LTP {self.ltp_value} with latest candle high {latest_candle['High']}")

                # Implement your comparison logic here
                signal, price, index_info = await async_return(
                    self.indicator.check_indicators(self.candle_data, self.token, self.ltp_value)
                )
                logger.info(f"Signal: {signal}, Price: {price}")
                if signal == Signal.BUY:
                    order_id, full_order_response = await async_return(self.data_provider.place_order(index_info[0], index_info[1], "BUY", "MARKET", price, "25"))
                    if full_order_response:
                        global_order_id = order_id
                        order_id, full_order_response = await async_return(self.data_provider.place_stoploss_limit_order(index_info[0], index_info[1], "25", price, (price*0.99)))
                        logger.info(f"STOPP_LOSS added, order_id")
                    logger.info(f"Order Status: {order_id} {full_order_response}")
                    await place_order_mail()
                    await save_order(order_id, full_order_response)
                elif signal == Signal.SELL:
                    order_id, full_order_response = await async_return(self.data_provider.place_order(index_info[0], index_info[1], "SELL", "MARKET", price, "25"))
                    logger.info(f"Order Status: {order_id} {full_order_response}")
                    await place_order_mail()
                    await save_order(order_id, full_order_response)
                elif signal == Signal.STOPLOSS:
                    order_id, full_order_response = await async_return(self.data_provider.modify_stoploss_limit_order(index_info[0], index_info[1], "25", price, price*0.99, order_id))
                    logger.info(f"Order Status: {order_id} {full_order_response}")
                    await place_order_mail()
                    await save_order(order_id, full_order_response)
            else:
                logger.info("Waiting for data...")

    async def start(self):
        try:
            while not self.stop_event.is_set():
                await self.fetch_candle_data()
                logger.info("fetch_candle_data continue")
                await asyncio.sleep(10)  # fetch candle data every 10 seconds
        except asyncio.CancelledError:
            logger.info("start task was cancelled")
            raise

    async def run(self):
        await asyncio.gather(
            self.fetch_ltp_data_continuous(),
            self.process_data(),
            self.start()
        )

    async def fetch_ltp_data_continuous(self):
        try:
            while not self.stop_event.is_set():
                await self.fetch_ltp_data()
                logger.info("fetch_ltp_data_continuous continues")
                await asyncio.sleep(1)  # fetch LTP data every second
        except asyncio.CancelledError:
            logger.info("fetch_ltp_data_continuous task was cancelled")
            raise

    async def stop(self):
        self.stop_event.set()

# Start strategy endpoint
@router.post("/start_strategy")
async def start_strategy(strategy_params: StartStrategySchema):
    try:
        strategy_id = strategy_params.strategy_id
        index_and_candle_durations = {
            f"{strategy_params.index}{strategy_params.expiry}{strategy_params.strike_price}{strategy_params.option}": strategy_params.chart_time,
        }
        # print("INDEX:DURATION", index_and_candle_durations)

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
        max_transactions_indicator = MaxMinOfLastTwo()
        strategy = BaseStrategy(instrument_reader, smart_api_provider, max_transactions_indicator, index_and_candle_durations)
        task = asyncio.create_task(strategy.run(), name=strategy_id)
        # await save_strategy(strategy_params)
        tasks[strategy_id] = task
        response = {
            "message": "strategy starts",
            "success": True,
            "strategy_id": strategy_id
        }
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


#get all trades with strik prices
@router.get("/get-margin-calculator")
def get_all_strike_prices():
    response = requests.get(NFO_DATA_URL)
    response.raise_for_status()
    data = response.json()
    with open("data.json", "w") as json_file:
        json.dump(data, json_file, indent=4)
    return {"message": "all strike list", "success": True}
