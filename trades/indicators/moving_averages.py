import datetime
import indicator_settings as ids
import statistics as stats
from collections import deque
from itertools import islice
import math
from .mcginley_indicator import McGinleyDynamicIndicator
from decimal import Decimal
class JurikMovingAverage():


    def __init__(self, timeframe, timestamp, jurik_period, phase, power, source):
        self.timestamp = timestamp
        self.jurik_period = jurik_period
        self.phase = phase
        self.power = power
        self.source = source

        self.timeframe = timeframe


        self.source_queue = deque(maxlen=self.jurik_period)

        self.jma = 0
        self.e0 = 0
        self.e1 = 0
        self.e2 = 0




        self.current_jurik = None
        self.current_value = None

        lens = [self.jurik_period]
        self.max_len = max(lens) * 2
        self.warmed_up = False
        self.value_queue = deque(maxlen=2)
        self.slope = None


    def calculate_value(self, open, high, low, close, volume, timestamp):
        if self.source == "CLOSE":
            src = close
        elif self.source == "OPEN":
            src = open
        elif self.source == "HIGH":
            src = high
        elif self.source == "LOW":
            src = low
        elif self.source == "HL2":
            src = (high + low) / 2
        elif self.source == "HLC3":
            src = (high + low + close) / 3
        elif self.source == "OHLC4":
            src = (open + high + low + close) / 4
        elif self.source == "HLCC4":
            src = (high + low + close + close) / 4
        else:
            raise Exception(f"Selected incorrect Source Value for BBWP, {self.source} is incorrect")

        self.source_queue.appendleft(src)
        if len(self.source_queue) == self.jurik_period:
            self.current_value = self.calculate_jurik(self.source_queue)
            self.value_queue.appendleft(self.current_value)
            if len(self.value_queue) == 2:
                x1, y1 = 0, self.value_queue[1]
                x2, y2 = 1, self.value_queue[0]
                self.slope = (y2 - y1) / (x2 - x1)

    def calculate_jurik(self, list_item):
        if self.phase < -100:
            phaseRatio = Decimal('0.5')
        elif self.phase > 100:
            phaseRatio = Decimal('2.5')
        else:
            phaseRatio = Decimal(self.phase) / Decimal('100') + Decimal('1.5')

        beta = Decimal('0.45') * (Decimal(len(list_item)) - Decimal('1')) / ( Decimal('0.45') * (Decimal(len(list_item)) - Decimal('1')) + Decimal('2'))

        alpha =beta**Decimal(self.power)
        self.e0 = (Decimal('1') - alpha) * Decimal(list_item[0]) + alpha * self.e0
        self.e1 = (Decimal(list_item[0]) - self.e0) * (Decimal('1') - beta) + beta * self.e1
        self.e2 = (self.e0 + phaseRatio * self.e1 - self.jma) * (Decimal('1') - alpha) ** Decimal(
            '2') + alpha ** Decimal('2') * self.e2
        self.jma = self.e2 + self.jma

        current_value = self.jma

        return current_value

class MCGinleyMovingAverage():


    def __init__(self, timeframe, timestamp, mcg_period, mcg_source, mcg_constant, mcg_average_mode):
        self.timestamp = timestamp
        self.mcg_period = mcg_period
        self.mcg = McGinleyDynamicIndicator(mcg_source, mcg_period, mcg_constant, mcg_average_mode)
        self.current_mcg = None
        self.timeframe = timeframe
        self.current_value = None
        lens = [self.mcg_period]
        self.max_len = max(lens) * 2
        self.warmed_up = False
        self.value_queue = deque(maxlen=2)
        self.slope = None

    def calculate_value(self, open, high, low, close, volume, timestamp):
        self.mcg.calculate_value(open, high, low, close, timestamp)
        self.current_mcg = self.mcg.mg
        self.current_value = self.current_mcg
        self.value_queue.appendleft(self.current_value)
        if len(self.value_queue) == 2:
            x1, y1 = 0, self.value_queue[1]
            x2, y2 = 1, self.value_queue[0]
            self.slope = (y2 - y1) / (x2 - x1)

class KaufmannMovingAverage():


    def __init__(self, timeframe, timestamp, kama_period):
        self.timestamp = timestamp
        self.kama_period = kama_period
        self.current_kama = None
        self.timeframe = timeframe
        self.xvnoise_queue = deque(maxlen=self.kama_period)
        self.source_queue = deque(maxlen=self.kama_period)

        self.current_value = None

        lens = [self.kama_period]
        self.max_len = max(lens) * 2
        self.warmed_up = False
        self.value_queue = deque(maxlen=2)
        self.slope = None

    def calculate_kma(self, list_item):
        xvnoise = abs(list_item[0] - list_item[1])
        self.xvnoise_queue.appendleft(xvnoise)

        if len(self.xvnoise_queue) == self.kama_period:

            nAMA = Decimal('0.0')
            nfastend = Decimal('0.666')
            nslowend = Decimal('0.0645')
            Length = len(list_item)

            # Get the absolute difference between the last element and the element at index Length
            nsignal = abs(Decimal(list_item[0]) - Decimal(list_item[Length - 1]))
            nnoise = sum([Decimal(x) for x in self.xvnoise_queue])
            nefratio = nsignal / nnoise if nnoise != Decimal('0') else Decimal('0')
            nsmooth = (nefratio * (nfastend - nslowend) + nslowend) ** Decimal('2')
            if self.current_kama is None:
                self.current_kama = Decimal('0')
            self.current_kama = self.current_kama + nsmooth * (Decimal(list_item[0]) - self.current_kama)
            return self.current_kama
    def calculate_value(self, open, high, low, close, volume, timestamp):
        self.source_queue.appendleft(close)
        if len(self.source_queue) == self.kama_period:
            self.current_value = self.calculate_kma(self.source_queue)
            if self.current_value is not None:
                self.value_queue.appendleft(self.current_value)
                if len(self.value_queue) == 2:
                    x1, y1 = 0, self.value_queue[1]
                    x2, y2 = 1, self.value_queue[0]
                    self.slope = (y2 - y1) / (x2 - x1)

class DoubleExponentialMovingAverage():


    def __init__(self, timeframe, timestamp, dema_period):
        self.timestamp = timestamp
        self.dema_period = dema_period
        self.current_dema = None
        self.timeframe = timeframe
        self.e1_queue = deque(maxlen=self.dema_period)
        self.e1 = None
        self.source_queue = deque(maxlen=self.dema_period)
        self.current_value = None

        lens = [self.dema_period]
        self.max_len = max(lens) * 4
        self.warmed_up = False
        self.value_queue = deque(maxlen=2)
        self.slope = None

    def calculate_dema(self, list_item_1):
        self.e1 = self.calculate_ema(list_item_1, self.e1)
        self.e1_queue.appendleft(self.e1)
        current_value = None
        self.value_queue.appendleft(self.current_value)
        if len(self.value_queue) == 2:
            x1, y1 = 0, self.value_queue[0]
            x2, y2 = 1, self.value_queue[1]
            self.slope = (y2 - y1) / (x2 - x1)

        return current_value


    def calculate_value(self, open, high, low, close, volume, timestamp):
        self.source_queue.appendleft(close)
        if len(self.source_queue) == self.dema_period:
            self.current_value = self.calculate_dema(self.source_queue)
            self.value_queue.appendleft(self.current_value)
            if len(self.value_queue) == 2:
                x1, y1 = 0, self.value_queue[1]
                x2, y2 = 1, self.value_queue[0]
                self.slope = (y2 - y1) / (x2 - x1)

class SmoothedMovingAverage():


    def __init__(self, timeframe, timestamp, smma_period):
        self.timestamp = timestamp
        self.smma_period = smma_period
        self.current_smma = None
        self.timeframe = timeframe
        self.current_value = None
        self.source_queue = deque(maxlen=self.smma_period)
        lens = [self.smma_period]
        self.max_len = max(lens) * 2
        self.warmed_up = False
        self.value_queue = deque(maxlen=2)
        self.slope = None

    def calculate_smma(self, list_item, current_value):
        length = len(list_item)
        outer = sum(list_item) / length
        if current_value is None:
            return outer
        else:
            current_value = (current_value * (length - 1) + list_item[-1]) / length
            return current_value


    def calculate_value(self, open, high, low, close, volume, timestamp):
        self.source_queue.appendleft(close)
        if len(self.source_queue) == self.smma_period:
            self.current_value = self.calculate_smma(self.source_queue, self.current_value)
            self.value_queue.appendleft(self.current_value)
            if len(self.value_queue) == 2:
                x1, y1 = 0, self.value_queue[1]
                x2, y2 = 1, self.value_queue[0]
                self.slope = (y2 - y1) / (x2 - x1)

class VolumeWeightedMovingAverage():


    def __init__(self, timeframe, timestamp, vwma_period):
        self.timestamp = timestamp
        self.vwma_period = vwma_period
        self.current_vwma = None
        self.timeframe = timeframe
        self.current_value = None
        self.volume_price_queue = deque(maxlen=self.vwma_period)
        self.volume_queue = deque(maxlen=self.vwma_period)

        lens = [self.vwma_period]
        self.max_len = max(lens) * 2
        self.warmed_up = False
        self.value_queue = deque(maxlen=2)
        self.slope = None

    def calculate_vwma(self, list_item_1, list_item_2):
        current_value = self.calculate_sma(list_item_1) / self.calculate_sma(list_item_2)

        return current_value


    def calculate_sma(self, list_item):
        current_value = sum(list_item) / len(list_item)
        return current_value


    def calculate_value(self, open, high, low, close, volume, timestamp):
        self.volume_price_queue.appendleft(volume*close)
        self.volume_queue.appendleft(volume)

        if len(self.volume_price_queue) == self.vwma_period and len(self.volume_queue) == self.vwma_period:
            self.current_value = self.calculate_vwma(self.volume_price_queue, self.volume_queue)
            self.value_queue.appendleft(self.current_value)
            if len(self.value_queue) == 2:
                x1, y1 = 0, self.value_queue[1]
                x2, y2 = 1, self.value_queue[0]
                self.slope = (y2 - y1) / (x2 - x1)

class ExponentialMovingAverage():


    def __init__(self, timeframe, timestamp, ema_period):
        self.timestamp = timestamp
        self.ema_period = ema_period
        self.current_ema = None
        self.timeframe = timeframe
        self.current_value = None
        self.source_queue = deque(maxlen=self.ema_period)

        lens = [self.ema_period]
        self.max_len = max(lens) * 2
        self.warmed_up = False
        self.value_queue = deque(maxlen=2)
        self.slope = None

    def calculate_ema(self, list_item, current_value):
        if current_value is None:
            current_value = list_item[0]
            return current_value
        else:
            alpha = Decimal(2 / (len(list_item) + 1))
            current_value = alpha * list_item[0] + (1 - alpha) * current_value
            return current_value


    def calculate_value(self, open, high, low, close, volume, timestamp):
        self.source_queue.appendleft(close)

        if len(self.source_queue) == self.ema_period:
            self.current_value = self.calculate_ema(self.source_queue, self.current_value)
            self.value_queue.appendleft(self.current_value)
            if len(self.value_queue) == 2:
                x1, y1 = 0, self.value_queue[1]
                x2, y2 = 1, self.value_queue[0]
                self.slope = (y2 - y1) / (x2 - x1)



class SimpleMovingAverage():
    def __init__(self, timeframe, timestamp, sma_period):
        self.timestamp = timestamp
        self.sma_period = sma_period
        self.timeframe = timeframe
        self.source_queue = deque(maxlen=self.sma_period)
        self.current_sma = None
        self.current_value = None
        lens = [self.sma_period]
        self.max_len = max(lens) * 2
        self.warmed_up = False
        self.value_queue = deque(maxlen=2)
        self.slope = None
    def calculate_value(self, open, high, low, close, volume, timestamp):
        self.source_queue.appendleft(close)
        if len(self.source_queue) == self.sma_period:
            self.current_value = self.calculate_sma(self.source_queue)

            self.value_queue.appendleft(self.current_value)
            if len(self.value_queue) == 2:
                x1, y1 = 0, self.value_queue[1]
                x2, y2 = 1, self.value_queue[0]
                self.slope = (y2 - y1) / (x2 - x1)

    def calculate_sma(self, list_item):
        current_value = sum(list_item) / len(list_item)
        return current_value



class VolumeWeightedExponentialMovingAverage:
    def __init__(self, timeframe, timestamp, vwema_period):
        self.timeframe = timeframe
        self.timestamp = timestamp
        self.vwema_period = vwema_period
        lens = [self.vwema_period]
        self.max_len = max(lens) * 2
        self.src_queue = deque(maxlen=self.vwema_period)
        self.vol_queue = deque(maxlen=self.vwema_period)
        self.current_value = None

    def calculate_vwema(self):
        if len(self.src_queue) < self.vwema_period:
            return None

        weighted_src = [src * vol for src, vol in zip(self.src_queue, self.vol_queue)]
        total_vol = sum(self.vol_queue)

        if total_vol == 0:
            return None

        weighted_avg_src = sum(weighted_src) / total_vol

        if self.current_value is None:
            self.current_value = weighted_avg_src
        else:
            alpha = Decimal(2 / (self.vwema_period + 1))
            self.current_value = alpha * weighted_avg_src + (1 - alpha) * self.current_value
        print(f'current_value {self.current_value} time {datetime.datetime.now()}')
        return self.current_value

    def calculate_value(self, open, high, low, close, volume, timestamp):
        src = (high + low + close) / 3 
        vol = volume  
        print(f'volume {volume}')
        self.src_queue.appendleft(src)
        self.vol_queue.appendleft(vol)

        return self.calculate_vwema()






