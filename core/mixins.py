from datetime import datetime
from uuid import uuid4

from sqlalchemy import Column, DateTime, String
from sqlalchemy.ext.declarative import declarative_base, declared_attr

Base = declarative_base()


class Timestamp:
    @declared_attr
    def created_at(cls):
        return Column(DateTime, default=datetime.utcnow, nullable=False)

    @declared_attr
    def updated_at(cls):
        return Column(DateTime, default=datetime.utcnow, nullable=False)


class UUIDModel:
    @declared_attr
    def id(cls):
        return Column(String, primary_key=True, default=str(uuid4()), index=True)


class CoreBaseModel(Timestamp, UUIDModel):
    pass
