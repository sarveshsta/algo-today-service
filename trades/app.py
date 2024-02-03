import time
from datetime import datetime, timedelta

import pandas as pd
import requests
from SmartApi import SmartConnect

from trades.token import Token


class SmartAPIException(Exception):
    """
    Custom exception raised for Smart API.
    """

    ...


class App:
    def __init__(self, user, api_key) -> None:
        self.__user = user
        self.__api_key = api_key

        self.__smart = SmartConnect(self.__api_key)
        self.__url_for_instruments = (
            "https://margincalculator.angelbroking.com/OpenAPI_File/files/OpenAPIScripMaster.json"
        )
        self.__instrument_list = []

    def start_session(self) -> dict:
        attempts = 5

        def request_for_session() -> dict:
            nonlocal attempts  # Use nonlocal for nested function scoping
            while attempts > 0:
                attempts -= 1
                try:
                    data = self.__smart.generateSession(self.__user.user_id, self.__user.password, self.__user.totp)
                except Exception as e:  # Catch any errors during session generation
                    print(f"Error during session generation: {e}")
                    time.sleep(5)  # Delay for 5 seconds before retrying
                    continue  # Skip to the next iteration of the loop

                if data["status"]:
                    __JWT_TOKEN = data["data"]["refreshToken"]
                    __FEED_TOKEN = self.__smart.getfeedToken()
                    return {
                        "status": "success",
                        "data": data,
                        "additionalData": {"JWT": __JWT_TOKEN, "FEED": __FEED_TOKEN},
                    }

                time.sleep(5)  # Delay before the next attempt

            return {"status": "error"}

        return request_for_session()

    def download_and_update_instrument_list(self) -> None:
        self.__instrument_list.clear()
        self.__instrument_list = requests.get(self.__url_for_instruments).json()

    def get_options_map(self, exch_type="NFO", opt_type="OPTIDX") -> list:
        instrument_list = self.__instrument_list
        options_map = []

        for instrument in instrument_list:
            st1 = instrument["exch_seg"] == exch_type
            st2 = instrument["instrumenttype"] == opt_type
            if st1 and st2:
                options_map.append(instrument)

        return options_map

    def get_candle_data(self, token: Token, interval: str = "ONE_MINUTE") -> pd.DataFrame:
        to_date = datetime.now()
        from_date = to_date - timedelta(days=5)
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
        df = pd.DataFrame(res_json["data"], columns=columns)
        return df
