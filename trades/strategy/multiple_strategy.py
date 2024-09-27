from datetime import datetime, timedelta
from enum import Enum
from typing import List
import pandas as pd
from config.database.config import SessionLocal
import os
import logging



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

class Token:
    def __init__(self, exch_seg: str, token_id: str, symbol: str):
        self.exch_seg = exch_seg
        self.token_id = token_id
        self.symbol = symbol

    def __str__(self):
        return f"{self.exch_seg}:{self.token_id}:{self.symbol}"

class Signal(Enum):
    BUY = 1
    MODIFY = 2
    WAITING_TO_BUY = 3
    WAITING_TO_MODIFY = 4
    NULL = 5
    SELL = 6
    WAITING_TO_SELL = 7
    WAITING_FOR_MODIFY_OR_SELL = 8

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


class IndicatorInterface:
    def check_indicators(
        self, data: pd.DataFrame, passed_token: Token, ltp_value: float, strategy_id: int, index: int = 0
    ) -> tuple[Signal, float, List[str]]:
        raise NotImplementedError("Subclasses must implement check_indicators()")


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
    def check_indicators(self, data: pd.DataFrame, passed_token: Token, ltp_value: float,  strategy_id: str, index: int = 0):
        ltp = ltp_value

        token = str(passed_token).split(":")[-1]  # this is actually symbol written as FINNIFTY23JUL2423500CE
        symbol_token = str(passed_token).split(":")[
            1
        ]  # a five digit integer number to represent the actual token number for the symbol
        index_info = [token, symbol_token, ltp]
        print(f"Check indicROETS {strategy_id} - {type(strategy_id)}")
        try:
            # checking for pre buying condition
            if strategy_id == "1":
                if self.waiting_for_buy == True:

                    current_candle = data.iloc[1]  # latest candle formed
                    previous_candle = data.iloc[2]  # last second candle formed
                   
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
                if not self.to_buy and token == self.trade_details["index"]:
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


                # direct selling condition
                if not self.waiting_for_buy:
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
