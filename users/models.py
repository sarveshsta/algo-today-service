import uuid
from sqlalchemy import Column, String, Boolean, Table,Text, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID
from config.database.config import Base
from sqlalchemy.orm import relationship
class User(Base):
    __tablename__ = 'algo_app_user'  # Replace with the actual table name (usually appname_modelname)

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(50), nullable=False, default="")
    phone = Column(String(50), nullable=False, unique=True, index=True, default="")
    email = Column(String, nullable=False, unique=True, default="")
    username = Column(String(20), nullable=True, default=None)

    is_active = Column(Boolean, default=True)
    is_staff = Column(Boolean, default=False)
    is_superuser = Column(Boolean, default=False)
    # models/user.py

    # Inside your User class:
    angelone_credentials = relationship("AngelOneCredential", uselist=False, back_populates="user")




class AngelOneCredential(Base):
    __tablename__ = "algo_app_angelonecredential"  
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("algo_app_user.id"), primary_key=True)  
    client_code = Column(String(50), nullable=False)
    password = Column(Text, nullable=False)
    totp_secret = Column(Text, nullable=False)
    jwt_token = Column(Text, nullable=True)
    feed_token = Column(Text, nullable=True)
    token_expiry = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)

    # Optional: Add relationship to User model
    user = relationship("User", back_populates="angelone_credentials")