from datetime import datetime
import pandas as pd
from typing import List
import logging
from .constant import *
from .common_strategy_fun import write_logs, Token, Signal

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class IndicatorInterface:
    def check_indicators(self, data: pd.DataFrame, passed_token: Token, ltp_value: float, index: int = 0) -> tuple[Signal, float, List[str]]:
        raise NotImplementedError("Subclasses must implement check_indicators()")

# main class of strategy
class MultiIndexStrategy(IndicatorInterface):
    to_buy = False
    to_sell = False
    waiting_for_sell = False
    waiting_for_buy = True
    stop_loss = False
    price = 0
    trading_price = 0
    number_of_candles = 5
    stop_loss_info = None
    trade_details = {"success": False, "index": None, "datetime": datetime.now()}

    # this is our main strategy function
    def check_indicators(self, data: pd.DataFrame, passed_token: Token, ltp_value: float, index: int = 0):
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

                        self.price = max_high
                        self.trading_price = max_high
                        self.trade_details["index"] = token

                        logger.info(f"Condition matched  {self.price}")
                        break

            # buying conditions
            if not self.to_buy and token == self.trade_details["index"]:
                if ltp*1000 > (1.01 * self.price):
                    self.to_buy = True
                    self.waiting_for_sell = True

                    self.to_sell = False
                    self.waiting_for_buy = False
                    self.price = ltp
                    self.trade_details["success"] = True
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

                    return (Signal.BUY, self.price, index_info)
                return (Signal.WAITING_TO_BUY, self.price, index_info)

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
                    return (Signal.STOPLOSS, self.price, index_info)

            elif not self.to_sell and self.to_buy and not self.waiting_for_buy:
                self.waiting_for_sell = True
                logger.info(f"TRADE DETAILS {self.trade_details}")
                return Signal.WAITING_TO_SELL, self.price, index_info

            else:
                self.waiting_for_buy = True
                self.trade_details["success"] = False
                logger.info(f"TRADE DETAILS {self.trade_details}")
                return Signal.WAITING_TO_BUY, self.price, index_info
        except Exception as exc:
            logger.error(f"An error occurred while checking indicators: {exc}")
            return (None, 0, [])
