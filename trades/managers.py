import requests
from fastapi import Depends
from sqlalchemy.orm import Session

from config.constants import EXCH_TYPE, NFO_DATA_URL, OPT_TYPE
from config.database.config import get_db
from trades.models import TokenModel
from trades.schema import TokenSchema


def get_tokens(db: Session = Depends(get_db), skip: int = 0, limit: int = 100):
    tokens = db.query(TokenModel).offset(skip).limit(limit).all()
    return tokens


def delete_all_tokens(db: Session = Depends(get_db)):
    db.query(TokenModel).delete()
    db.commit()
    return True


def fetch_tokens(db: Session = Depends(get_db)):
    url = NFO_DATA_URL
    response = requests.get(url)
    data = response.json()

    for instrument in data:
        st1 = instrument["exch_seg"] == EXCH_TYPE
        st2 = instrument["instrumenttype"] == OPT_TYPE
        if st1 and st2:
            db_token = TokenModel(**instrument)
            db.add(db_token)
            db.commit()


def retrieve_token(symbol: str, db: Session = Depends(get_db)):
    token = db.query(TokenModel).filter(TokenModel.symbol == symbol).first()
    if token:
        return token
    return None
