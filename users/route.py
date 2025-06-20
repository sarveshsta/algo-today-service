import pyotp
import fastapi
from typing import List
from pydantic import BaseModel
from sqlalchemy.orm import Session
from config.database.config import get_db
from fastapi import Depends, HTTPException
from fastapi.responses import JSONResponse
from .models import User, AngelOneCredential
from SmartApi.smartConnect import SmartConnect
from middlewares.auth_middleware import verify_token
from users.schema import UserCreateSchema, UserDetailSchema, UserSchema, AngelOneLoginRequest
from users.manager import create_user, get_users, get_user_by_id
from utils import response

router = fastapi.APIRouter()
API_KEY = "ZlQnOy4h"  



@router.post("/connect-account")
def connect_angleone(data: AngelOneLoginRequest):
    try:
        smart_api = SmartConnect(api_key=API_KEY)
        totp = pyotp.TOTP(data.totp_secret).now()
        session = smart_api.generateSession(data.client_code, data.password, totp)
        profile = smart_api.getProfile(session['data']['refreshToken'])
        return response(True, {"session": session,"profile": profile}, "AngelOne account connected successfully")
    except Exception as e:
        return response(message="Login failed", error=str(e))



@router.get("/angelone-credentials")
def get_all_angelone_credentials(db: Session = Depends(get_db)):
    try:
        credentials = db.query(AngelOneCredential).all()
        return response(True, credentials, "data retirve success")
    except Exception as e:
        print(str(e), "error")
        return response(error=str(e))


@router.get("/{user_id}")
def read_user(user_id: str, db: Session = Depends(get_db)):
    try:
        user = get_user_by_id(user_id, db)
        return response(True, user, "user retrieve success")
    except Exception as e:
        print(str(e), "error")
        return response(error=str(e))


