from decouple import config


class InitSettings:
    def __init__(self) -> None:
        self.API_KEY = config("API_KEY")
        self.ID = config("ID")
        self.PASSWORD = config("PASSWORD")
        self.OTP_CODE = config("OTP_CODE")

        print(f"Got settings for Account {self.ID}")
