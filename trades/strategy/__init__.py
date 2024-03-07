import threading
import time
from datetime import datetime, timedelta
from enum import Enum
from json.decoder import JSONDecodeError
from typing import List
from urllib.error import URLError

import pandas as pd
import requests, pyotp
from SmartApi import SmartConnect

from config.constants import SERVICE_NAME
from core.events import TradeEvent
from core.redis import PubSubClient
from trades.indicators import IndicatorInterface, Signal, MaxMinOfLastTwo


class CandleDuration(Enum):
    ONE_MINUTE = "ONE_MINUTE"
    THREE_MINUTE = "THREE_MINUTE"
    FIVE_MINUTE = "FIVE_MINUTE"
    TEN_MINUTE = "TEN_MINUTE"


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

    def fetch_candle_data(
        self, token: Token, duration: int = 5, interval: CandleDuration = CandleDuration.ONE_MINUTE
    ) -> pd.DataFrame:
        to_date = datetime.now()
        from_date = to_date - timedelta(minutes=duration)
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


class PublisherInterface:
    publisher = None

    def publish(self, data: dict):
        raise NotImplementedError("Subclasses must implement publish()")


class RedisPublisherInterface(PublisherInterface):
    def __init__(self, pubsub: PubSubClient) -> None:
        self.publisher = pubsub

    def publish(self, data: dict):
        self.publisher.publish(SERVICE_NAME, data)


class BaseStrategy:
    def _init_(
        self,
        instrument_reader: InstrumentReaderInterface,
        data_provider: DataProviderInterface,
        indicator: IndicatorInterface,
        publisher: PublisherInterface,
    ):
        self.instruments = instrument_reader.read_instruments()
        self.data_provider = data_provider
        self.indicator = indicator
        self.publisher = publisher

    def signal(self, direction: str, price: float) -> None:
        # Placeholder method to send signals to the event bus
        event = TradeEvent({"signal": direction, "price": price})
        self.publisher.publish(event.to_json())

    def process_data(self, index: int):
        # Fetch data for all tokens
        nfo_tokens = [Token(instrument.exch_seg, instrument.token) for instrument in self.instruments]
        data = {token: self.data_provider.fetch_candle_data(token) for token in nfo_tokens}
        for token, token_data in data.items():
            signal, price = self.indicator.check_indicators(token_data, index)

            match(signal):
                case Signal.BUY:
                    self.signal("BUY", price)
                case Signal.SELL:
                    self.signal("SELL", price)
                case Signal.WAITING_TO_BUY:
                    self.signal("WAITING_TO_BUY", price)
                case Signal.WAITING_TO_SELL:
                    self.signal("WAITING_TO_SELL", price)
                case _:
                    # Implement the logic if require to handle
                    pass

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
    totp=pyotp.TOTP(token_code).now(),
)
auth_token = data["data"]["jwtToken"]
feed_token = smart.getfeedToken()

instrument_reader = OpenApiInstrumentReader(NFO_DATA_URL, ["BANKNIFTY06MAR2447000CE"])
smart_api_provider = SmartApiDataProvider(smart)
max_transactions_indicator = MaxMinOfLastTwo()
strategy = BaseStrategy(instrument_reader, smart_api_provider, max_transactions_indicator)
strategy.start_strategy()