import logging
from typing import Dict, List
from enum import Enum
import os
from datetime import datetime
import asyncio

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


# class CandleDuration(Enum):
#     ONE_MINUTE = "ONE_MINUTE"
#     THREE_MINUTE = "THREE_MINUTE"
#     FIVE_MINUTE = "FIVE_MINUTE"
#     TEN_MINUTE = "TEN_MINUTE"


class Signal(Enum):
    BUY = 1
    SELL = 2
    WAITING_TO_BUY = 3
    WAITING_TO_SELL = 4
    STOPLOSS = 5

class Token:
    def __init__(self, exch_seg: str, token_id: str, symbol: str):
        self.exch_seg = exch_seg
        self.token_id = token_id
        self.symbol = symbol

    def __str__(self):
        return f"{self.exch_seg}:{self.token_id}:{self.symbol}"

def async_return(result):
    obj = asyncio.Future()
    obj.set_result(result)
    return obj   

class SignalTrigger:
    def __init__(self, data_provider) -> None:
        self.data_provider = data_provider
    async def signal_trigger(self, data_provider, index_info, price, quantity, signal, order_id=None):
        if signal == Signal.BUY:
            logger.info(f"signal buy")
            # order_id, full_order_response = await async_return(data_provider.place_order(index_info[0], index_info[1], "BUY", "MARKET", price, quantity))
            # if full_order_response:
            #     order_id, full_order_response = await async_return(data_provider.place_stoploss_limit_order(index_info[0], index_info[1], quantity, price, (price*0.99)))

        elif signal == Signal.SELL:
            logger.info(f"signal sell")
            # order_id, full_order_response = await async_return(data_provider.place_order(index_info[0], index_info[1], "SELL", "MARKET", price, quantity))

        elif signal == Signal.STOPLOSS:
            logger.info(f"signal stoploss")
        #     order_id, full_order_response = await async_return(data_provider.modify_stoploss_limit_order(index_info[0], index_info[1], quantity, price, price*0.99, order_id))
        # await place_order_mail()
        # await save_order(order_id, full_order_response)
        return "order_id"

class FetchCandleLtpValeus:
    def __init__(self, index_candle_durations, data_provider, instruments, token):
        self.index_candle_durations = index_candle_durations
        self.data_provider = data_provider
        self.instruments = instruments
        self.gen_token = token
        self.token_value: Dict[str, token] = {}

    def fetch_ltp_data(self):
        index_ltp_values: Dict[str, float] = {}
        try:
            for instrument in self.instruments:
                data = ltp_candle_values(self.index_candle_durations, "LTP", instrument, self.data_provider, self.gen_token)
                if data[f"{str(instrument.symbol)}_sym"] is None:
                    continue
                index_ltp_values[str(instrument.symbol)] = data[f"{str(instrument.symbol)}_sym"]
                self.token_value[str(instrument.symbol)] = data[f"{str(instrument.symbol)}_token"]
                
            return (index_ltp_values, self.token_value)
        except Exception as e:
            logger.error(f"An error occurred while fetching LTP data: {e}")

    def fetch_candle_data(self):
        index_candle_data: List[tuple] = []

        # index_candle_data = {str, list}
        try:
            for instrument in self.instruments:
                data = ltp_candle_values(self.index_candle_durations, "CANDLE", instrument, self.data_provider, self.gen_token)
                if data[f"{str(instrument.symbol)}_sym"] is None:
                    continue
                index_candle_data.append((str(instrument.symbol), data[f"{str(instrument.symbol)}_sym"]))
                self.token_value[str(instrument.symbol)] = data[f"{str(instrument.symbol)}_token"]
            return (index_candle_data, self.token_value)
        except logging.exception:
            logger.error(f"An error occurred while fetching candle data")


def ltp_candle_values(index_candle_durations, tradetype, instrument, data_provider, gen_token):
    data_dict = {}
    token = gen_token(instrument.exch_seg, instrument.token, instrument.symbol)
    data_dict[f"{str(instrument.symbol)}_token"] = token
    if tradetype == "LTP":
        ltp_data = data_provider.fetch_ltp_data(token)
        if "data" not in ltp_data.keys():
            data_dict[f"{str(instrument.symbol)}_sym"] = None
        data_dict[f"{str(instrument.symbol)}_sym"] = float(ltp_data["data"]["ltp"])
    elif tradetype == "CANDLE":
        candle_duration = index_candle_durations[instrument.symbol]
        candle_data = data_provider.fetch_candle_data(token, interval=candle_duration)
        # candle_data = async_return(candle_data)
        if candle_data is None:
            data_dict[f"{str(instrument.symbol)}_sym"] = None
        data_dict[f"{str(instrument.symbol)}_sym"] = candle_data
    return data_dict
