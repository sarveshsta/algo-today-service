import threading
import time
from datetime import datetime, timedelta
from enum import Enum
from json.decoder import JSONDecodeError
from typing import List, Union
from urllib.error import HTTPError, URLError

import pandas as pd
import pandas_ta as ta
import pyotp
import requests
from SmartApi import SmartConnect

# from config.constants import API_KEY, CLIENT_CODE, PASSWORD, TOKEN_CODE


class CandleDuration(Enum):
    ONE_MINUTE = "ONE_MINUTE"
    THREE_MINUTE = "THREE_MINUTE"
    FIVE_MINUTE = "FIVE_MINUTE"
    TEN_MINUTE = "TEN_MINUTE"


class Signal(Enum):
    BUY = 1
    SELL = 2
    WAITING_TO_BUY = 3
    WAITING_TO_SELL = 4


class Token:
    def __init__(self, exch_seg: str, token_id: str):
        self.exch_seg = exch_seg
        self.token_id = token_id

    def __str__(self):
        return f"{self.exch_seg}:{self.token_id}"


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
            response.raise_for_status()  # Raise an exception for HTTP errors
            data = response.json()
            return [
                Instrument(**item)
                for item in data
                if item["exch_seg"] == "NFO" and item["symbol"] in self.tokens  # Filter for NFO instruments only
            ]
        except (URLError, JSONDecodeError) as e:
            print(f"Error reading instruments from {self.url}: {e}")
            return []
    

class DataProviderInterface:
    def fetch_candle_data(self, token: Token, interval: str = "ONE_MINUTE") -> pd.DataFrame:
        raise NotImplementedError("Subclasses must implement fetch_candle_data()")


class SmartApiDataProvider(DataProviderInterface):
    def __init__(self, smart: SmartConnect):
        self.__smart = smart

    def fetch_candle_data(self, token: Token, interval: str = "ONE_MINUTE") -> pd.DataFrame:
        to_date = datetime.now()
        from_date = to_date - timedelta(minutes=5)
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
        data = pd.DataFrame(res_json["data"], columns=columns)
        print("Data Provided: ", data)
        return data


class IndicatorInterface:
    def check_indicators(self, data: pd.DataFrame) -> List[str]:
        raise NotImplementedError("Subclasses must implement check_indicators()")

class MaxMinOfLastTwo(IndicatorInterface):
    DOUBLE_HIGH_MULTIPLIER = 1.012
    DOUBLE_LOW_MULTIPLIER = 0.988
    SINGLE_LOW_MULTIPLIER = 1.032
    SINGLE_HIGH_MULTIPLIER = 0.968
    to_buy = False
    to_sell = False
    waiting_for_sell = False
    waiting_for_buy = False
    price = 0
    sold_price = 0
    cum_profit = 0
    trades_count = 0
    current_index = 0
    LAST_OHLC = 4
    SECOND_LAST_OHLC = 5
    CURRENT_OHLC = 5


    def check_indicators(self, data: pd.DataFrame, index: int = 0) -> tuple[Signal, float]:
        current_open = data["Open"].iloc[self.CURRENT_OHLC]
        last_third_open = data["Open"].iloc[self.CURRENT_OHLC - 2]
        print("LATEST/LAST CANDLE OPEN", f"{current_open} ** {last_third_open}")

        # condition to buy
        if not self.to_buy:
            if current_open >= (last_third_open + (last_third_open * 0.01)):
                self.to_buy = True
                self.waiting_for_sell = True

                self.to_sell = False
                self.waiting_for_buy = False
                self.price = current_open
                return Signal.BUY, self.price
            return Signal.WAITING_TO_BUY, self.price
        
        # condition to sell 
        elif self.to_buy and not self.to_sell and self.waiting_for_sell:
            if (data["High"].iloc[self.CURRENT_OHLC - 2] >= self.price * 1.10) or \
                    (data["Low"].iloc[self.CURRENT_OHLC - 2] <= self.price * 0.95):
                self.to_sell = True
                self.waiting_for_buy = True

                self.to_buy = False
                self.waiting_for_sell = False

                return Signal.SELL, self.price
            return Signal.WAITING_TO_SELL, self.price

        elif not self.to_sell and self.to_buy and not self.waiting_for_buy:
            self.waiting_for_sell = True
            return Signal.WAITING_TO_SELL, self.price
        
        else:
            self.waiting_for_buy = True
            return Signal.WAITING_TO_BUY, self.price
            
  
class BaseStrategy:
    def __init__(
        self,
        instrument_reader: InstrumentReaderInterface,
        data_provider: DataProviderInterface,
        indicator: IndicatorInterface,
    ):
        self.instruments = instrument_reader.read_instruments()
        self.data_provider = data_provider
        self.indicator = indicator

    def signal(self, direction: str):
        # Placeholder method to send signals to the event bus
        print(f"Sending {direction} signal to event bus")

    def process_data(self, index: int):
        # Fetch data for all tokens
        nfo_tokens = [Token(instrument.exch_seg, instrument.token) for instrument in self.instruments]
        data = {token: self.data_provider.fetch_candle_data(token) for token in nfo_tokens}
        for token, token_data in data.items():
            signal, price = self.indicator.check_indicators(token_data, index)
            print("_" * 10)
            print("Signal: ", signal)
            print("Price: ", price)
            print("Data: ", token_data.iloc[index])
            print("Time: ", token_data.iloc[index]["timestamp"])
            print("_" * 10)

    def start_strategy(self):
        index = 0
        # Start the data processing thread
        self.data_processing_thread = threading.Thread(target=self.process_data, args=(index,))
        self.data_processing_thread.start()
        # Start a loop to periodically call self.process_data
        while True:
            self.process_data(index)
            time.sleep(50)
            index += 1


NFO_DATA_URL = "https://margincalculator.angelbroking.com/OpenAPI_File/files/OpenAPIScripMaster.json"
OPT_TYPE = "OPTIDX"
EXCH_TYPE = "NFO"

API_KEY = "T4MHVpXH"
CLIENT_CODE = "J263557"
PASSWORD = "7753"
TOKEN_CODE = "3MYXRWJIJ2CZT6Y5PD2EU5RNNQ"

api_key = API_KEY
token_code = TOKEN_CODE
client_code = CLIENT_CODE
password = PASSWORD

smart = SmartConnect(api_key=api_key)
data = \
    smart.generateSession(
    clientCode=client_code,
    password=password,
    totp=pyotp.TOTP(token_code).now()
)
auth_token = data["data"]["jwtToken"]
feed_token = smart.getfeedToken()

instrument_reader = OpenApiInstrumentReader(NFO_DATA_URL, ["BANKNIFTY03APR2444400PE"])
smart_api_provider = SmartApiDataProvider(smart)
max_transactions_indicator = MaxMinOfLastTwo()
strategy = BaseStrategy(instrument_reader, smart_api_provider, max_transactions_indicator)
strategy.start_strategy()