from decouple import config

DATABASE_URI = config("DATABASE_URI")

REDIS_HOST = config("REDIS_HOST")
REDIS_PORT = config("REDIS_PORT", cast=int)
