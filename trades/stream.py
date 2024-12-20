import asyncio
import threading

import pyotp
from SmartApi import SmartConnect
from SmartApi.smartWebSocketV2 import SmartWebSocketV2

from core.events import SmartAPIEvent
from core.redis import PubSubClient


# client code to get LTP data
LTP_API_KEY = "MolOSZTR"
LTP_CLIENT_CODE = "S55329579"
LTP_PASSWORD = "4242"
LTP_TOKEN_CODE = "QRLYAZPZ6LMTH5AYILGTWWN26E"

class WSApp:
    def __init__(
        self,
        api_key: str,
        token_code: str,
        client_code: str,
        password: str,
        token_listener: list,
        pubsub: PubSubClient,
    ) -> None:
        self.api_key = api_key
        self.token_listener = token_listener
        self.pubsub = pubsub
        smart = SmartConnect(api_key=self.api_key)
        data = smart.generateSession(
                clientCode=LTP_CLIENT_CODE, password=LTP_PASSWORD, totp=pyotp.TOTP(LTP_TOKEN_CODE).now()
            )
        auth_token = data["data"]["jwtToken"]
        feed_token = smart.getfeedToken()

        self.sws = SmartWebSocketV2(
            auth_token=auth_token,
            api_key=self.api_key,
            client_code=client_code,
            feed_token=feed_token,
        )

        self._token_list = []

        # Assign the callbacks
        self.sws.on_open = self.on_open
        self.sws.on_data = self.on_data
        self.sws.on_error = self.on_error
        self.sws.on_close = self.on_close

        # Start the asyncio event loop in a separate thread
        self.loop_thread = threading.Thread(target=self.start_event_loop, daemon=True)
        self.loop_thread.start()

    def start_event_loop(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()

    def on_data(self, wsapp, message):
        event = SmartAPIEvent(message)
        try:
            asyncio.run_coroutine_threadsafe(
                self.publish_to_redis(self.pubsub, event, event.to_json()), self.loop
            ).result()
        except Exception as e:
            print(e)

    async def publish_to_redis(self, pubsub: PubSubClient, event: SmartAPIEvent, message: dict):
        await event.activity(pubsub, message)

    def on_open(self, wsapp):
        token_list = self.token_listener or []
        self.sws.subscribe("abc123", 2, token_list)

    def on_error(self, wsapp, error):
        self.loop.stop()

    def on_close(self, wsapp):
        self.loop.stop()

    def close_connection(self):
        self.sws.close_connection()

    def connect(self):
        try:
            self.connect_thread = threading.Thread(target=self.sws.connect, daemon=True)
            self.connect_thread.start()
        except Exception as e:
            print(e)
