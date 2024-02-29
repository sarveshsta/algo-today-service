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
    def __init__(self, url: str, tokens: List[str] = None):
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
        from_date = to_date - timedelta(days=5)
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
    bought_price = 0
    sold_price = 0
    cum_profit = 0
    trades_count = 0
    current_index = 0

    def check_indicators(self, data: pd.DataFrame, index: int = 0) -> tuple[Signal, float]:
        if index == 2:
            previous_max_high = max(data["High"].iloc[index - 1], data["High"].iloc[index - 2])
            new_high = previous_max_high * self.DOUBLE_HIGH_MULTIPLIER

            self.to_buy = False
            self.to_sell = False
            self.waiting_for_buy = True
            self.bought_price = new_high
            return Signal.WAITING_TO_BUY, self.bought_price
        if index > 2:
            if not self.to_buy and not self.to_sell and self.waiting_for_buy:
                if data["High"].iloc[index] > self.bought_price:
                    self.to_buy = False
                    self.to_sell = True
                    self.waiting_for_buy = False
                    return Signal.SELL, self.bought_price

                if self.waiting_for_buy:
                    previous_max_high = (
                        max(data["High"].iloc[index - 1], data["High"].iloc[index - 2]) * self.DOUBLE_HIGH_MULTIPLIER
                    )
                    previous_high = (data["High"].iloc[index - 1]) * self.SINGLE_HIGH_MULTIPLIER
                    new_high = min(previous_max_high, previous_high)
                    if new_high != self.bought_price:
                        self.bought_price = new_high
                        return Signal.WAITING_TO_BUY, self.bought_price

            elif not self.to_buy and self.to_sell:
                last_two_low = []
                last_two_low.append(data["Low"].iloc[index - 2])
                last_two_low.append(data["Low"].iloc[index - 1])
                min_last_two_low = self.DOUBLE_LOW_MULTIPLIER * min(last_two_low)
                previous_low = (data["Low"].iloc[index - 1]) * self.SINGLE_LOW_MULTIPLIER
                new_low = max(min_last_two_low, previous_low)
                self.sold_price = new_low
                self.to_buy = False
                self.to_sell = False
                self.waiting_for_sell = True
                return Signal.WAITING_TO_SELL, self.sold_price

            elif not self.to_buy and not self.to_sell and self.waiting_for_sell:
                if data["Low"].iloc[index] < self.sold_price:
                    self.trades_count += 1
                    self.to_buy = True
                    self.to_sell = False
                    self.waiting_for_sell = False
                    return Signal.BUY, self.sold_price
                if self.waiting_for_sell:
                    last_two_low = []
                    last_two_low.append(data["Low"].iloc[index - 2])
                    last_two_low.append(data["Low"].iloc[index - 1])
                    min_last_two_low = self.DOUBLE_LOW_MULTIPLIER * min(last_two_low)
                    previous_low = (data["Low"].iloc[index - 1]) * self.SINGLE_LOW_MULTIPLIER
                    new_low = max(min_last_two_low, previous_low)
                    if new_low != self.sold_price:
                        self.sold_price = new_low
                        return Signal.WAITING_TO_SELL, self.sold_price

            elif self.to_buy and not self.to_sell:
                previous_max_high = max(data["High"].iloc[index - 1], data["High"].iloc[index - 2])
                new_high = previous_max_high * self.DOUBLE_HIGH_MULTIPLIER
                self.to_buy = False
                self.to_sell = False
                self.waiting_for_buy = True
                self.bought_price = new_high
                return Signal.WAITING_TO_BUY, self.bought_price

        return None, None


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
            print(signal, price)
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

API_KEY = None
CLIENT_CODE = None
PASSWORD = None
TOKEN_CODE = None

api_key = API_KEY
token_code = TOKEN_CODE
client_code = CLIENT_CODE
password = PASSWORD

smart = SmartConnect(api_key=api_key)
data = smart.generateSession(
    clientCode=client_code,
    password=password,
    totp=pyotp.TOTP(token_code).now(),
)
auth_token = data["data"]["jwtToken"]
feed_token = smart.getfeedToken()

instrument_reader = OpenApiInstrumentReader(NFO_DATA_URL, ["BANKNIFTY29FEB2446800CE"])
smart_api_provider = SmartApiDataProvider(smart)
max_transactions_indicator = MaxMinOfLastTwo()
strategy = BaseStrategy(instrument_reader, smart_api_provider, max_transactions_indicator)
strategy.start_strategy()
