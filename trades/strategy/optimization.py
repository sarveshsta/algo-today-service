import asyncio
import json
import logging
from datetime import datetime, timedelta
from json.decoder import JSONDecodeError
from typing import Dict, List
from urllib.error import URLError

import pandas as pd
import requests
from SmartApi import SmartConnect
from .constant import *
from .common_strategy_fun import async_return, FetchCandleLtpValeus, SignalTrigger, Token, Signal
from .multipleIndexStrategy import IndicatorInterface


# https://pypi.org/project/smartapi-python/
# objects to get `@smart` candle data and `@ltp_smart`LTP data respectively

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)



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
        data = res_json['data'][::-1]
        return data[:15]

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
            order_book = self.__smart.orderBook()
            for i in order_book['data']:
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


# to access objects of dataframe and dict kind

class BaseStrategy:
    def __init__(
        self,
        instrument_reader: InstrumentReaderInterface,
        data_provider: DataProviderInterface,
        indicator: IndicatorInterface,
        index_candle_durations: Dict[str, str],
        extra_args: dict
    ):
        self.instruments = instrument_reader.read_instruments()
        self.data_provider = data_provider
        self.indicator = indicator
        self.index_candle_durations = index_candle_durations
        self.ltp_comparison_interval = 2
        self.order_id = int
        self.index_candle_data: Dict[str, tuple] = {}
        self.index_ltp_values: Dict[str, float] = {}
        self.token_value: Dict[str, Token] = {}
        self.stop_event = asyncio.Event()
        self.parameters = extra_args
        self.fetch_candle_ltp = FetchCandleLtpValeus(self.index_candle_durations, self.data_provider, self.instruments, Token)
        self.signal_trigger = SignalTrigger(self.data_provider)



    async def process_data(self):
        for index, value in self.index_candle_data:
            await asyncio.sleep(1)
            if (value and self.index_ltp_values[index]) is not None:
                logger.info(f"token1: {self.token_value[index]}, quantity1: {self.parameters[index]}")

                columns = ["timestamp", "Open", "High", "Low", "Close", "Volume"]
                data = pd.DataFrame(value, columns=columns)
                latest_candle = data.iloc[1]
                logger.info(f"Comparing LTP {self.index_ltp_values[index]} with latest candle high {latest_candle['High']}")

                # Implement your comparison logic here
                signal, price, index_info = await async_return(
                    self.indicator.check_indicators(data, self.token_value[index], self.index_ltp_values[index])
                )
                logger.info(f"Signal: {signal}, Price: {price}")
                if signal in [Signal.BUY, Signal.SELL, Signal.STOPLOSS]:
                    self.order_id = await self.signal_trigger.signal_trigger(self.data_provider, index_info, price, self.parameters[index], signal, self.order_id)  
            else:
                logger.info("Waiting for data...")

    async def fetch_candle_data_continuous(self):
        try:
            while not self.stop_event.is_set():
                self.index_candle_data, self.token_value = await async_return(self.fetch_candle_ltp.fetch_candle_data())
                logger.info("fetch_candle_data continue")
                await asyncio.sleep(10)  # fetch candle data every 10 seconds
        except asyncio.CancelledError:
            logger.info("start task was cancelled")
            raise

    async def fetch_ltp_data_continuous(self):
        try:
            while not self.stop_event.is_set():
                self.index_ltp_values, self.token_value = await async_return(self.fetch_candle_ltp.fetch_ltp_data())
                logger.info("fetch_ltp_data_continuous continues")
                await asyncio.sleep(1)  # fetch LTP data every second
        except asyncio.CancelledError:
            logger.info("fetch_ltp_data_continuous task was cancelled")
            raise

    async def process_data_continuous(self):
        try:
            while not self.stop_event.is_set():
                await self.process_data()
                logger.info("process_data_continuous continues")
                await asyncio.sleep(1)  # fetch LTP data every second
        except asyncio.CancelledError:
            logger.info("process_data_continuous task was cancelled")
            raise

    async def run(self):
        await asyncio.gather(
            self.fetch_ltp_data_continuous(),
            self.process_data_continuous(),
            self.fetch_candle_data_continuous()
        )

    async def stop(self):
        self.stop_event.set()

