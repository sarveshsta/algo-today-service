import indicator_settings as ids
import statistics as stats
from collections import deque
from itertools import islice
import math
from .moving_averages import ExponentialMovingAverage
from decimal import Decimal

class StandardDeviationIndicator():


    def __init__(self, timeframe, timestamp, length):
        self.timeframe = timeframe
        self.timestamp = timestamp
        self.length = length
        print(length)
        self.close_queue = deque(maxlen=self.length)

        self.current_value = None
        self.warmed_up = False

        lens = [self.length]
        self.max_len = max(lens) * 2


    def isZero(self, val, eps):
        absolute_value = abs(val)
        if absolute_value <= eps:
            return True
        else:
            return False


    def SUM(self, fst, snd):
        EPS = 1e-10
        res = fst + snd
        if self.isZero(res, EPS):
            res = 0
        else:
            if not self.isZero(res, 1e-4):
                res = res
            else:
                res = 15
        return res



    def pine_stdev(self, list_item, length):
        avg = Decimal(sum(list_item) / len(list_item))
        sumOfSquareDeviations = Decimal(0)

        for i in range(length):
            sum_ = self.SUM(list_item[i], -avg)
            sumOfSquareDeviations = sumOfSquareDeviations + sum_ * sum_


        stdev = math.sqrt(sumOfSquareDeviations / length)

        return Decimal(stdev)



    def calculate_value(self, open, high, low, close, volume, timestamp):
        self.close_queue.appendleft(close)

        if len(self.close_queue) == self.length:
            self.current_value =  self.pine_stdev(self.close_queue, self.length)