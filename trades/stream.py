from logzero import logger
from SmartApi.smartWebSocketV2 import SmartWebSocketV2


class WSApp:
    def __init__(
        self,
        user,
        api_key,
    ) -> None:
        self.user = user
        self.api_key = api_key
        self.sws = SmartWebSocketV2(
            auth_token=self.user.jwt,
            api_key=self.api_key,
            client_code=self.user.user_id,
            feed_token=self.user.feed_token,
        )

        self._token_list = []

        # Assign the callbacks
        self.sws.on_open = self.on_open
        self.sws.on_data = self.on_data
        self.sws.on_error = self.on_error
        self.sws.on_close = self.on_close

    def on_data(self, wsapp, message):
        logger.info("Ticks: {}".format(message))

    def on_open(self, wsapp):
        logger.info("on open")
        token_list = self.get_token_list() or []
        self.sws.subscribe(self.user.user_id, 1, token_list)

    def on_error(self, wsapp, error):
        logger.error(error)

    def on_close(self, wsapp):
        logger.info("Close")

    def close_connection(self):
        self.sws.close_connection()

    def connect(self):
        self.sws.connect()

    def get_token_list(self):
        return self._token_list

    def set_token_list(self, token_list):
        self._token_list = token_list

    def validate_and_add_token(self, exchange_type, token):
        if self.validate_token(exchange_type, token):
            self._token_list.append({"exchangeType": exchange_type, "tokens": [token]})
        else:
            logger.error(f"Invalid token: {token}")

    def validate_token(self, exchange_type, token):
        if exchange_type == 1:  # Assuming 1 represents a specific exchange type
            # Perform validation specific to exchange type 1
            # Return True if the token is valid, False otherwise
            return True
        else:
            return False
