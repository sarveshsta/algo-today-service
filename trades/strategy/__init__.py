import threading, time
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
from datetime import datetime


class CandleDuration(Enum):
    ONE_MINUTE = "ONE_MINUTE"
    THREE_MINUTE = "THREE_MINUTE"
    FOUR_MINUTE = "FOUR_MINUTE"
    FIVE_MINUTE = "FIVE_MINUTE"
    TEN_MINUTE = "TEN_MINUTE"

# variables initialisation start
indexes_list = ["MIDCPNIFTY29APR2410700PE", "NIFTY25APR2422200CE"]
index_candle_durations = {
    "MIDCPNIFTY22APR2410725PE": CandleDuration.ONE_MINUTE,
    "NIFTY25APR2422200CE": CandleDuration.THREE_MINUTE
}

# price comparision
OHLC_1 =  "Close"
OHLC_2 =  "High"

# buying condition comparision
buying_multiplier = 1.01
buying_OHLC = "High"

# selling condition comparision
trail_ltp_multiplier = 1.12
price_vs_ltp_mulitplier = 1.10

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

class Token:
    def __init__(self, exch_seg: str, token_id: str, symbol:str):
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
            # print("Response", response)
            response.raise_for_status()
            data = response.json()
            return [
                Instrument(**item)
                for item in data
                if item["exch_seg"] == "NFO" and item["symbol"] in self.tokens
            ]
        except (URLError, JSONDecodeError) as e:
            print(f"Error reading instruments from {self.url}: {e}")
            return []
    
class DataProviderInterface:
    def fetch_candle_data(self, token: Token, interval: str = "ONE_MINUTE", symvol:str="") -> pd.DataFrame:
        raise NotImplementedError("Subclasses must implement fetch_candle_data()")

class SmartApiDataProvider(DataProviderInterface):
    def __init__(self, smart: SmartConnect, ltpSmart: SmartConnect):
        self.__smart = smart
        self.__ltpSmart = ltpSmart

    def fetch_candle_data(self, token, interval) -> pd.DataFrame:
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

        ltp_data = self.__ltpSmart.ltpData("NFO", token.symbol, token.token_id)
        data['LTP'] = float(ltp_data['data']['ltp'])      
        return data
    
    def fetch_ltp_data(self, token):
        ltp_data = self.__ltpSmart.ltpData("NFO", token.symbol, token.token_id)
        return float(ltp_data['data']['ltp'])    

class IndicatorInterface:
    def check_indicators(self, data: pd.DataFrame) -> List[str]:
        raise NotImplementedError("Subclasses must implement check_indicators()")


class MaxMinOfLastTwo(IndicatorInterface):
    to_buy = False
    to_sell = False
    waiting_for_sell = False
    waiting_for_buy = True
    price = 0
    number_of_candles = 3
    trade_details = {"done":False,"index":None,'datetime':datetime.now(),"price":price,'type':None}

    def check_indicators(self, data: pd.DataFrame, token:str,  index: int = 0) -> tuple[Signal, float]:
        ltp_price = float(data['LTP'][0])
        token = str(token).split(':')[-1]
        print("TOKEN", token)
        print("DATA:", data)
        if self.trade_details['index'] == None or self.waiting_for_buy==True:
            if self.number_of_candles > len(data): self.number_of_candles= len(data) - 1 
            print("NUMBER OF CANDLES", self.number_of_candles)
            print("DATA length", len(data))

            for i in range(len(data) - 1, 0, -1):
            # for i in range(len(data)-1, 0, -1):
                current_candle = data.iloc[i]
                previous_candle = data.iloc[i - 1]

                print(f'C{i} => {current_candle[OHLC_1]} H{i-1} => {previous_candle[OHLC_2]}')

                if current_candle[OHLC_1] >= previous_candle[OHLC_2]:
                    high_values = [data.iloc[j][OHLC_2] for j in range(i, len(data)-1)]
                    # Find the maximum high value
                    max_high = max(high_values)
                    # Update self.price with the maximum high value
                    self.price = max_high

                    self.price = current_candle[OHLC_2]
                    self.trade_details['index'] = token
                    self.trade_details['price'] = self.price
                    print("Condition matched", self.price)
                    break

        current_high = data[buying_OHLC].iloc[-2]

        if not self.to_buy and token == self.trade_details['index']:
            if ltp_price > self.price * buying_multiplier:
                self.to_buy = True
                self.waiting_for_sell = True

                self.to_sell = False
                self.waiting_for_buy = False
                self.price = current_high
                self.trade_details['done'] = True
                self.trade_details['index'] = str(token)
                self.trade_details['datetime'] = datetime.now()
                self.trade_details = {"done": False, "index": None, 'datetime': datetime.now()}
                print("TRADE BOUGHT in",token, self.trade_details)
                return Signal.BUY, self.price
                
            elif self.price >= current_high * buying_multiplier:
                self.to_buy = True
                self.waiting_for_sell = True

                self.to_sell = False
                self.waiting_for_buy = False
                self.price = current_high
                self.trade_details['done'] = True
                self.trade_details['index'] = str(token)
                self.trade_details['datetime'] = datetime.now()
                self.trade_details = {"done": False, "index": None, 'datetime': datetime.now()}
                print("TRADE BOUGHT in",token, self.trade_details)
                return Signal.BUY, self.price
            return Signal.WAITING_TO_BUY, self.price
        
        elif self.to_buy and not self.to_sell and self.waiting_for_sell \
            and self.trade_details['index'] == token:

            if ltp_price >= trail_ltp_multiplier * self.price:
                print("TRADE DETAILS", self.trade_details)
                return Signal.WAITING_TO_SELL, self.price
            
            elif ltp_price < self.price * price_vs_ltp_mulitplier:
                self.to_sell = True
                self.waiting_for_buy = True

                self.to_buy = False
                self.waiting_for_sell = False
                self.price = ltp_price
                self.trade_details['datetime'] = datetime.now()
                self.trade_details['index'] = None
                self.trade_details['price'] = self.price
                print("LTP PRICE and Selling price", ltp_price, self.price)
                print("TRADE SOLD", token, self.trade_details)
                return Signal.SELL, self.price
            
            if (data[selling_OHLC1].iloc[-1] >= self.price * selling_OHLC1_multiplier):
                self.to_sell = True
                self.waiting_for_buy = True

                self.to_buy = False
                self.waiting_for_sell = False
                self.price = data[selling_OHLC1].iloc[-1]
                self.trade_details['price'] = self.price
                self.trade_details['datetime'] = datetime.now()
                self.trade_details['index'] = None
                print("TRADE SOLD", self.trade_details)
                return Signal.SELL, self.price 
            
            elif (data[selling_OHLC2].iloc[-1] <= self.price * selling_OHLC2_multiplier):
                
                self.to_sell = True
                self.waiting_for_buy = True

                self.to_buy = False
                self.waiting_for_sell = False
                self.price = data[selling_OHLC2].iloc[-1]
                self.trade_details['price'] = self.price
                self.trade_details['datetime'] = datetime.now()
                self.trade_details['index'] = None
                print("Selling price", self.price)
                print("TRADE SOLD", self.trade_details)
                return Signal.SELL, self.price
            return Signal.WAITING_TO_SELL, self.price
        
        elif not self.to_sell and self.to_buy and not self.waiting_for_buy:
            self.waiting_for_sell = True
            print("TRADE DETAILS", self.trade_details)
            return Signal.WAITING_TO_SELL, self.price
        
        else:
            self.waiting_for_buy = True
            self.trade_details['done'] = False
            self.trade_details['index'] = None
            print("TRADE DETAILS", self.trade_details)
            return Signal.WAITING_TO_BUY, self.price
  
class BaseStrategy:
    def __init__(
        self,
        instrument_reader: InstrumentReaderInterface,
        data_provider: DataProviderInterface,
        indicator: IndicatorInterface,
        index_candle_durations: dict[str, CandleDuration]
    ):
        self.instruments = instrument_reader.read_instruments()
        self.data_provider = data_provider
        self.indicator = indicator # Initialize self.price and load trade details from database
        self.index_candle_durations = index_candle_durations

    def signal(self, direction: str):
        print(f"Sending {direction} signal to event bus")

    def process_data(self, index: int):
        for instrument in self.instruments:
            token = Token(instrument.exch_seg, instrument.token, instrument.symbol)
            candle_duration = self.index_candle_durations.get(instrument.symbol, CandleDuration.ONE_MINUTE)
            token_data = self.data_provider.fetch_candle_data(token, interval=candle_duration.value)
            ltp = self.data_provider.fetch_ltp_data(token)
            signal, price = self.indicator.check_indicators(token_data, token, index)
            print("_" * 10)
            print("Signal: ", signal)
            print("Price: ", price)
            print("Data: ", token_data.iloc[index])
            print("Token: ", token)
            print("Time: ", token_data.iloc[index]["timestamp"])
            print("_" * 10)
            time.sleep(3)
        # self.nfo_tokens = [Token(instrument.exch_seg, instrument.token, instrument.symbol) for instrument in self.instruments]
        # self.data = {token: self.data_provider.fetch_candle_data(token) for token in self.nfo_tokens}
        # for token, token_data in self.data.items():
        #     signal, price = self.indicator.check_indicators(token_data, token,  index)
        #     print("_" * 10)
        #     print("Signal: ", signal)
        #     print("Price: ", price)
        #     print("Data: ", token_data.iloc[index])
        #     print("Token: ", token)
        #     print("Time: ", token_data.iloc[index]["timestamp"])
        #     print("_" * 10)
        

    def continuously_fetch_ltp_data(self):
        while True:
            for instrument in self.instruments:
                token = Token(instrument.exch_seg, instrument.token, instrument.symbol)
                ltp = self.data_provider.fetch_ltp_data(token)  # Fetch LTP
                print(f"LTP for {instrument.symbol}: {ltp}")
            
            time.sleep(3)

    def start_strategy(self):
        index = -1
        threading.Thread(target=self.continuously_fetch_ltp_data, args=()).start()
        self.data_processing_thread = threading.Thread(target=self.process_data, args=(index))
        # threading.Timer(3, self.process_data, args=(index,)).start()
        
        while True:
            self.process_data(index)
            time.sleep(50)
            if not index > 2: 
                index += 1
            else: index = index


NFO_DATA_URL = "https://margincalculator.angelbroking.com/OpenAPI_File/files/OpenAPIScripMaster.json"
OPT_TYPE = "OPTIDX"
EXCH_TYPE = "NFO"

API_KEY = "T4MHVpXH"
CLIENT_CODE = "J263557"
PASSWORD = "7753"
TOKEN_CODE = "3MYXRWJIJ2CZT6Y5PD2EU5RNNQ"
LTP_API_KEY = "FJrreQAW"

api_key = API_KEY
token_code = TOKEN_CODE
client_code = CLIENT_CODE
password = PASSWORD
ltp_api_key = LTP_API_KEY


smart = SmartConnect(api_key=api_key)
ltp_smart = SmartConnect(api_key=api_key)

data = smart.generateSession(
    clientCode=client_code,
    password=password,
    totp=pyotp.TOTP(token_code).now()
)
ltp_data = ltp_smart.generateSession(
    clientCode=client_code,
    password=password,
    totp=pyotp.TOTP(token_code).now()
)
try: 
    auth_token = data["data"]["jwtToken"]
    auth_token = ltp_data["data"]["jwtToken"]
except: print("Access denied, exceeding access rate")

feed_token = smart.getfeedToken() 

instrument_reader = OpenApiInstrumentReader(NFO_DATA_URL, indexes_list)
smart_api_provider = SmartApiDataProvider(smart, ltp_smart)
max_transactions_indicator = MaxMinOfLastTwo()
strategy = BaseStrategy(instrument_reader, smart_api_provider, max_transactions_indicator, index_candle_durations)
strategy.start_strategy()
