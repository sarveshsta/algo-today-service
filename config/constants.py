from decouple import config

DATABASE_URI = config("DATABASE_URI")

REDIS_HOST = config("REDIS_HOST")
REDIS_PASSWORD = config("REDIS_PASSWORD")
REDIS_PORT = config("REDIS_PORT", cast=int)

NFO_DATA_URL = config("NFO_DATA_URL")
OPT_TYPE = config("OPT_TYPE")
EXCH_TYPE = config("EXCH_TYPE")

API_KEY = config("API_KEY")
CLIENT_CODE = config("CLIENT_CODE")
PASSWORD = config("PASSWORD")
TOKEN_CODE = config("TOKEN_CODE")

SERVICE_NAME = config("SERVICE_NAME")
