import asyncio
from datetime import datetime, timedelta
from enum import Enum
from json.decoder import JSONDecodeError
from typing import List
from urllib.error import URLError
import logging
import pandas as pd
import pyotp
import requests
from SmartApi import SmartConnect
from datetime import datetime
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def write_logs(type, index, price, status, reason):
    log_dir = "logs/trade"
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

# variables initialisation start
indexes_list = ["NIFTY20JUN2421500PE"]
index_candle_durations = {
    indexes_list[0]: CandleDuration.THREE_MINUTE,
}
 
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
            return [Instrument(**item) for item in data if item["exch_seg"] == "NFO" and item["symbol"] in self.tokens]
        except (URLError, JSONDecodeError) as e:
            print(f"Error reading instruments from {self.url}: {e}")
            return []


class DataProviderInterface:
    def fetch_candle_data(self, token: Token, interval: str = "ONE_MINUTE", symvol: str = "") -> pd.DataFrame:
        raise NotImplementedError("Subclasses must implement fetch_candle_data()")

    def fetch_ltp_data(self, token: Token, interval: str = "ONE_MINUTE", symvol: str = "") -> pd.DataFrame:
        raise NotImplementedError("Subclasses must implement fetch_ltp_data()")

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
        return pd.DataFrame(res_json["data"], columns=columns)

    def fetch_ltp_data(self, token):
        ltp_data = self.__ltpSmart.ltpData("NFO", token.symbol, token.token_id)
        return ltp_data
    
    def place_order(self, symbol, token, transaction, price, quantity):
        try:
            orderparams ={
                "variety": "NORMAL",
                "tradingsymbol": symbol,
                "symboltoken": token,
                "transactiontype": transaction,
                "exchange": "NFO",
                "ordertype": "MARKET",
                "producttype": "INTRADAY",
                "duration": "DAY",
                "price": price,
                "squareoff": "0",
                "stoploss": "0",
                "quantity": quantity,
            }
            orderId = self.__smart.placeOrder(orderparams)
            print(f"The order id is: {orderId}")
            return orderId
        except Exception as e:
            print(f"Order placement failed: {e}")
            return False


class IndicatorInterface:
    def check_indicators(self, data: pd.DataFrame) -> List[str]:
        raise NotImplementedError("Subclasses must implement check_indicators()")

# main class of strategy 
class MaxMinOfLastTwo(IndicatorInterface):
    to_buy = False
    to_sell = False
    waiting_for_sell = False
    waiting_for_buy = True
    price = 0
    trading_price = 0
    number_of_candles = 10
    trade_details = {"done":False, "index":None, 'datetime':datetime.now()}
    
    # this is our main strategy function
    def check_indicators(self, data: pd.DataFrame, token:str,  index: int = 0) -> tuple[Signal, float]:
        ltp = float(data['LTP'][0])
        token = str(token).split(':')[-1]
        print("TOKEN", token)
        print("DATA:", data[0:15])
        
        # checking for pre buying condition
        if self.waiting_for_buy == True:
            if self.number_of_candles > len(data)-2: self.number_of_candles= len(data) - 2 

            for i in range(1, self.number_of_candles+1):
                current_candle = data.iloc[i]
                previous_candle = data.iloc[i + 1]

                print(f'C{i} => {current_candle[OHLC_1]} H{i+1} => {previous_candle[OHLC_2]}')

                if current_candle[OHLC_1] >= previous_candle[OHLC_2]:
                    high_values = [float(data.iloc[j][OHLC_2]) for j in range(i, 0, -1)]
                    max_high = max(high_values)
                    print("HIGH VALUES", high_values)

                    self.price = max_high
                    self.trading_price = max_high
                    self.trade_details['index'] = token

                    print("Condition matched", self.price)
                    break


        if not self.to_buy and token == self.trade_details['index']:
            if ltp > self.price:
                self.to_buy = True
                self.waiting_for_sell = True

                self.to_sell = False
                self.waiting_for_buy = False
                self.price = ltp
                self.trade_details['done'] = True
                self.trade_details['index'] = token

                self.trade_details['datetime'] = datetime.now()
                print("PRE CONDITION PRICE", self.trading_price, "CURRENT LTP", ltp)
                print("TRADE BOUGHT due to LTP > Price", self.trade_details)

                write_logs("BOUGHT", token, self.price, "NILL", f"LTP > condition matched self.price {self.trading_price}")

                return Signal.BUY, self.price
            return Signal.WAITING_TO_BUY, self.price
        
        elif self.to_buy and not self.to_sell and self.waiting_for_sell \
            and self.trade_details['index'] == token:

            if ltp >= 1.10 * self.price:
                self.to_sell = True
                self.waiting_for_buy = True

                self.to_buy = False
                self.waiting_for_sell = False
                print("LTP PRICE and Selling self.price", ltp, self.price)

                write_logs("SOLD", token, self.price, "Profit", f"LTP > 1.10* buying self.price -> {ltp} > {self.price}")

                self.price = ltp
                self.trade_details['datetime'] = datetime.now()
                self.trade_details['index'] = None
                print("TRADE SOLD PROFIT LTP", self.trade_details)

                return Signal.SELL, self.price
                # return Signal.WAITING_TO_SELL, self.price
            
            elif ltp < self.price * price_vs_ltp_mulitplier:
                self.to_sell = True
                self.waiting_for_buy = True

                self.to_buy = False
                self.waiting_for_sell = False
                print("LTP PRICE and Selling self.price", ltp, self.price)

                write_logs("SOLD", token, self.price, "Loss", f"LTP < {price_vs_ltp_mulitplier} * buying self.price {self.price}")

                self.price = ltp
                self.trade_details['datetime'] = datetime.now()
                self.trade_details['index'] = None
                print("TRADE SOLD LOSS LTP",self.trade_details)
                
                return Signal.SELL, self.price
            
            elif (data[selling_OHLC1].iloc[1] >= self.price * selling_OHLC1_multiplier):
                self.to_sell = True
                self.waiting_for_buy = True

                self.to_buy = False
                self.waiting_for_sell = False

                print("LTP PRICE and Selling self.price", data[selling_OHLC1].iloc[1], self.price)

                write_logs("SOLD", token, self.price, "Profit", f"Latest made candle High > 1.10*buying self.price -> {data[selling_OHLC1].iloc[1]} > {selling_OHLC1_multiplier} *{self.price}")

                self.price = data[selling_OHLC1].iloc[1]
                self.trade_details['datetime'] = datetime.now()
                self.trade_details['index'] = None
                print("TRADE SOLD PROFIT HIGH", self.trade_details)
                
                return Signal.SELL, self.price 
            
            elif (data[selling_OHLC2].iloc[1] <= self.price * selling_OHLC2_multiplier):
                
                self.to_sell = True
                self.waiting_for_buy = True

                self.to_buy = False
                self.waiting_for_sell = False
                print("LOW of candle and Selling self.price", data[selling_OHLC2].iloc[1], self.price)
                self.price = data[selling_OHLC2].iloc[1]


                write_logs("SOLD", token, self.price, "Loss", f"Latest made candle Low < 0.95*buying self.price -> {data[selling_OHLC2].iloc[1]} <= {selling_OHLC2_multiplier} {self.price}")

                self.trade_details['datetime'] = datetime.now()
                self.trade_details['index'] = None
                print("Selling self.price", self.price)
                print("TRADE SOLD LOSS LOW", self.trade_details)

                return Signal.SELL, self.price
            return Signal.WAITING_TO_SELL, self.price
        
        elif not self.to_sell and self.to_buy and not self.waiting_for_buy:
            self.waiting_for_sell = True
            print("TRADE DETAILS", self.trade_details)
            return Signal.WAITING_TO_SELL, self.price
        
        else:  
            self.waiting_for_buy = True
            self.trade_details['done'] = False
            print("TRADE DETAILS", self.trade_details)
            return Signal.WAITING_TO_BUY, self.price


#to access objects of dataframe and dict kind
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
        index_candle_durations: dict[str, CandleDuration],
    ):
        self.instruments = instrument_reader.read_instruments()
        self.data_provider = data_provider
        self.indicator = indicator
        self.index_candle_durations = index_candle_durations
        self.ltp_comparison_interval = 2
        self.candle_data = pd.DataFrame(columns=["timestamp", "Open", "High", "Low", "Close", "Volume"])
        self.ltp_value = None

    async def fetch_ltp_data(self):
        try:
            for instrument in self.instruments:
                token = Token(instrument.exch_seg, instrument.token, instrument.symbol)
                ltp_data = await async_return(self.data_provider.fetch_ltp_data(token))
                if 'data' not in ltp_data or 'ltp' not in ltp_data['data']:
                    logger.error("No 'ltp' key in the LTP response JSON")
                    continue  # Continue to the next instrument
                self.ltp_value = float(ltp_data["data"]["ltp"])
                logger.info(f"LTP Data Updated: {self.ltp_value}")
        except Exception as e:
            logger.error(f"An error occurred while fetching LTP data: {e}")


    async def fetch_candle_data(self):
        try:
            for instrument in self.instruments:
                token = Token(instrument.exch_seg, instrument.token, instrument.symbol)
                candle_duration = self.index_candle_durations.get(instrument.symbol, CandleDuration.THREE_MINUTE).value  # Default to "1min"
                candle_data = await async_return(self.data_provider.fetch_candle_data(token, interval=candle_duration))
                if candle_data.empty:
                    logger.error(f"No candle data returned for {instrument.symbol}")
                    continue  # Continue to the next instrument
                self.candle_data = candle_data
                logger.info(f"Candle Data Updated for {instrument.symbol}: {self.candle_data}")
        except Exception as e:
            logger.error(f"An error occurred while fetching candle data: {e}")

    async def process_data(self):
        while True:
            await asyncio.sleep(1)
            if not self.candle_data.empty and self.ltp_value is not None:
                latest_candle = self.candle_data.iloc[-1]
                logger.info(f"Comparing LTP {self.ltp_value} with latest candle close {latest_candle['Close']}")
                # Implement your comparison logic here
            else:
                logger.info("Waiting for data...")

    async def start_strategy(self):
        asyncio.create_task(self.fetch_ltp_data_continuous())
        asyncio.create_task(self.process_data())

        while True:
            await self.fetch_candle_data()
            await asyncio.sleep(10)  # fetch candle data every 10 seconds

    async def fetch_ltp_data_continuous(self):
        while True:
            await self.fetch_ltp_data()
            await asyncio.sleep(1)  # fetch LTP data every second

if __name__ == '__main__':
    NFO_DATA_URL = "https://margincalculator.angelbroking.com/OpenAPI_File/files/OpenAPIScripMaster.json"
    OPT_TYPE = "OPTIDX"
    EXCH_TYPE = "NFO"

    # creds to get candle data
    API_KEY = "T4MHVpXH"
    CLIENT_CODE = "J263557"
    PASSWORD = "7753"
    TOKEN_CODE = "3MYXRWJIJ2CZT6Y5PD2EU5RNNQ"

    # client code to get LTP data
    LTP_API_KEY = "MolOSZTR"
    LTP_CLIENT_CODE = "S55329579"
    LTP_PASSWORD = "4242"
    LTP_TOKEN_CODE = "QRLYAZPZ6LMTH5AYILGTWWN26E"

    api_key = API_KEY
    token_code = TOKEN_CODE
    client_code = CLIENT_CODE
    password = PASSWORD
    ltp_api_key = LTP_API_KEY

    # https://pypi.org/project/smartapi-python/
    # objects to get `@smart` candle data and `@ltp_smart`LTP data respectively
    smart = SmartConnect(api_key=api_key)
    ltp_smart = SmartConnect(api_key=LTP_API_KEY)
    
    ltp_data = ltp_smart.generateSession(
        clientCode=LTP_CLIENT_CODE, password=LTP_PASSWORD, totp=pyotp.TOTP(LTP_TOKEN_CODE).now()
    )

    try:
        data = smart.generateSession(clientCode=client_code, password=password, totp=pyotp.TOTP(token_code).now())
        auth_token = data["data"]["jwtToken"]
        auth_token = ltp_data["data"]["jwtToken"]
    except:
        print("Access denied, exceeding access rate")
        exit()

    feed_token = smart.getfeedToken()

    instrument_reader = OpenApiInstrumentReader(NFO_DATA_URL, indexes_list)
    smart_api_provider = SmartApiDataProvider(smart, ltp_smart)
    max_transactions_indicator = MaxMinOfLastTwo()
    strategy = BaseStrategy(instrument_reader, smart_api_provider, max_transactions_indicator, index_candle_durations)
    asyncio.run(strategy.start_strategy())
