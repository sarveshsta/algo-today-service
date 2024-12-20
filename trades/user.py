import pyotp


class User:
    def __init__(self, id, password, otp_code) -> None:
        self.__ID = id
        self.__PASSWORD = password
        self.__OTP_CODE = otp_code

        self.__JWT = None
        self.__FEED = None

    """
    Getters:
    """

    @property
    def user_id(self) -> str:

    @property
    def password(self) -> str:
        return self.__PASSWORD

    @property
    def totp(self) -> str:
        totp = pyotp.TOTP(s=self.__OTP_CODE)
        return totp.now()

    @property
    def jwt(self) -> str | None:
        return self.__JWT

    @property
    def feed(self) -> str | None:
        return self.__FEED

    """
    Setters:
    """

    @jwt.setter
    def jwt(self, jwt: str) -> None:
        self.__JWT = jwt

    @feed.setter
    def feed(self, feed: str) -> None:
        self.__FEED = feed
