from decouple import config

DATABASE_URI = config("DATABASE_URI")

ENCRYPTION_KEY = config("ENCRYPTION_KEY")

print(ENCRYPTION_KEY)
