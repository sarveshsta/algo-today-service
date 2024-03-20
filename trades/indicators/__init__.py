from enum import Enum
from typing import List

import pandas as pd


class Signal(Enum):
    BUY = 1
    SELL = 2
    WAITING_TO_BUY = 3
    WAITING_TO_SELL = 4


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
    LAST_OHLC = 4
    SECOND_LAST_OHLC = 5
    CURRENT_OHLC = 5

    def check_indicators(self, data: pd.DataFrame, index: int = 0) -> tuple[Signal, float]:
        if index == 2:
            previous_max_high = max(data["High"].iloc[self.LAST_OHLC], data["High"].iloc[self.SECOND_LAST_OHLC])
            new_high = previous_max_high * self.DOUBLE_HIGH_MULTIPLIER

            self.to_buy = False
            self.to_sell = False
            self.waiting_for_buy = True
            self.bought_price = new_high
            return Signal.WAITING_TO_BUY, self.bought_price
        if index > 2:
            if not self.to_buy and not self.to_sell and self.waiting_for_buy:
                if data["High"].iloc[self.CURRENT_OHLC] > self.bought_price:
                    self.to_buy = False
                    self.to_sell = True
                    self.waiting_for_buy = False
                    return Signal.SELL, self.bought_price

                if self.waiting_for_buy:
                    previous_max_high = (
                        max(data["High"].iloc[self.LAST_OHLC], data["High"].iloc[self.SECOND_LAST_OHLC])
                        * self.DOUBLE_HIGH_MULTIPLIER
                    )
                    previous_high = (data["High"].iloc[self.LAST_OHLC]) * self.SINGLE_HIGH_MULTIPLIER
                    new_high = min(previous_max_high, previous_high)
                    if new_high != self.bought_price:
                        self.bought_price = new_high
                        return Signal.WAITING_TO_BUY, self.bought_price

            elif not self.to_buy and self.to_sell:
                last_two_low = []
                last_two_low.append(data["Low"].iloc[self.SECOND_LAST_OHLC])
                last_two_low.append(data["Low"].iloc[self.LAST_OHLC])
                min_last_two_low = self.DOUBLE_LOW_MULTIPLIER * min(last_two_low)
                previous_low = (data["Low"].iloc[self.LAST_OHLC]) * self.SINGLE_LOW_MULTIPLIER
                new_low = max(min_last_two_low, previous_low)
                self.sold_price = new_low
                self.to_buy = False
                self.to_sell = False
                self.waiting_for_sell = True
                return Signal.WAITING_TO_SELL, self.sold_price

            elif not self.to_buy and not self.to_sell and self.waiting_for_sell:
                if data["Low"].iloc[self.CURRENT_OHLC] < self.sold_price:
                    self.trades_count += 1
                    self.to_buy = True
                    self.to_sell = False
                    self.waiting_for_sell = False
                    return Signal.BUY, self.sold_price
                if self.waiting_for_sell:
                    last_two_low = []
                    last_two_low.append(data["Low"].iloc[self.SECOND_LAST_OHLC])
                    last_two_low.append(data["Low"].iloc[self.LAST_OHLC])
                    min_last_two_low = self.DOUBLE_LOW_MULTIPLIER * min(last_two_low)
                    previous_low = (data["Low"].iloc[self.LAST_OHLC]) * self.SINGLE_LOW_MULTIPLIER
                    new_low = max(min_last_two_low, previous_low)
                    if new_low != self.sold_price:
                        self.sold_price = new_low
                        return Signal.WAITING_TO_SELL, self.sold_price

            elif self.to_buy and not self.to_sell:
                previous_max_high = max(data["High"].iloc[self.LAST_OHLC], data["High"].iloc[self.SECOND_LAST_OHLC])
                new_high = previous_max_high * self.DOUBLE_HIGH_MULTIPLIER
                self.to_buy = False
                self.to_sell = False
                self.waiting_for_buy = True
                self.bought_price = new_high
                return Signal.WAITING_TO_BUY, self.bought_price

        return None, None


class StrategyOne(IndicatorInterface):
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
    LAST_OHLC = 4
    SECOND_LAST_OHLC = 5
    CURRENT_OHLC = 5
