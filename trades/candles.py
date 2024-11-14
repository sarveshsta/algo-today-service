from datetime import datetime, timedelta

import aioredis
import pandas as pd


class CandleCache:
    def __init__(self):
        self.cache = {}

    def create_connection(self, host, port, password):
        self.client = aioredis.Redis.from_url(
            f"redis://{host}:{port}/", encoding="utf-8", decode_responses=True, password=password, ssl=False
        )
        return self.client

    def add_candles(self, token, candles):
        self.cache[token] = candles

    def get_last_15_candles(self, token):
        return self.cache.get(token, pd.DataFrame()).tail(15)

    def update_cache(self, token, new_candle):
        if token in self.cache:
            self.cache[token] = self.cache[token].append(new_candle, ignore_index=True).tail(15)
        else:
            self.cache[token] = pd.DataFrame([new_candle]).tail(15)
