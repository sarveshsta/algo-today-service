import indicator_settings as ids
import statistics as stats
from collections import deque
from decimal import Decimal

class VidyaIndicator():


    def __init__(self, timeframe, timestamp, vidya_period, vidya_history_period):
        self.timeframe = timeframe
        self.timestamp = timestamp
        self.period = vidya_period
        self.history_period = vidya_history_period

        self.price_queue = deque(maxlen=self.period)
        self.history_queue = deque(maxlen=self.history_period)
        self.current_value = 0

        lens = [self.period, self.history_period]
        self.max_len = max(lens) * 2
        self.warmed_up = False
        self.value_queue = deque(maxlen=2)
        self.slope = None

        self.mom_queue = deque(maxlen=self.period)


    def get_cmo(self, list_item):
        mom = list_item[0] - list_item[1]
        self.mom_queue.appendleft(mom)
        current_value = None
        if len(self.mom_queue) == self.period:
            upSum = 0
            for i in self.mom_queue:
                upSum += max(i, 0)

            downSum = 0
            for i in self.mom_queue:
                downSum += -(min(i, 0))

            out =  (upSum - downSum) / (upSum + downSum)
            current_value = out
        return current_value



    def calculate_value(self, open, high, low, close, volume, timestamp):
        self.price_queue.appendleft(close)
        self.history_queue.appendleft(close)
        if len(self.price_queue) == self.period and len(self.history_queue) == self.history_period:
            cmo = self.get_cmo(self.price_queue)
            if cmo is not None:
                cmo = abs(cmo)
                alpha = Decimal(2 / (self.period + 1))
                self.current_value = close * alpha * cmo + self.current_value * (1 - alpha * cmo)
                self.value_queue.appendleft(self.current_value)
                if len(self.value_queue) == 2:
                    x1, y1 = 0, self.value_queue[1]
                    x2, y2 = 1, self.value_queue[0]
                    self.slope = (y2 - y1) / (x2 - x1)