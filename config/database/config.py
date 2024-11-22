from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from config.constants import DATABASE_URI

#SQLALCHEMY_DATABASE_URL = DATABASE_URI
from sqlalchemy import create_engine
import os

# Replace the placeholders with your database information
DATABASE_URI = os.getenv("DATABASE_URI")

# Create the engine
engine = create_engine(DATABASE_URI)

#engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={}, future=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, future=True)

Base = declarative_base()


# DB Utilities
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
