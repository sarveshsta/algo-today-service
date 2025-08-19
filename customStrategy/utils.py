import os
import logging
import pytz
import pyotp
import pandas as pd
from time import sleep, time
from typing import List, Dict
from dotenv import load_dotenv
from sqlalchemy.orm import Session
from trades.models import TradeDetails, Trade, StrategyPayload
from datetime import datetime, timedelta
from SmartApi.smartConnect import SmartConnect
from config.database.config import SessionLocal
from users.models import User, AngelOneCredential
from trades.managers import get_token_uuid_by_token_value
from .instrument_utils import get_instruments_from_openapi


load_dotenv()
EXCHANGE_MAP = {"NSE": "NSE", "NFO": "NFO"}

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_user_credentials(db: Session, user_id: str) -> dict:
    credentials = db.query(AngelOneCredential).filter_by(user_id=user_id).first()
    return {
        "client_code": credentials.client_code,
        "password": credentials.password,
        "totp_secret": credentials.totp_secret,
        "api_key" : credentials.api_key 
    }


def get_smartapi_connection(credentials: Dict[str, str]) -> SmartConnect:
    if not credentials:
        raise ValueError("Missing credentials for SmartAPI connection")

    obj = SmartConnect(api_key=credentials['api_key'])
    totp = pyotp.TOTP(credentials['totp_secret']).now()
    obj.generateSession(credentials['client_code'],credentials['password'],totp)
    return obj


# Fetch candle data
# def get_candle_data(token: List[str], exchange: str, interval: str = "FIVE_MINUTE", days: int = 1, credentials: Dict[str, str] = None):
#     try:
#         smartapi = get_smartapi_connection(credentials)
#         ist = pytz.timezone('Asia/Kolkata')
#         to_date = datetime.now(ist)
#         from_date = to_date - timedelta(days=days)

#         params = {
#             "exchange": EXCHANGE_MAP[exchange],
#             "symboltoken": get_instruments_from_openapi(os.getenv("NFO_DATA_URL"), token)[0]['token'],
#             "interval": interval, 
#             "fromdate": from_date.strftime("%Y-%m-%d %H:%M"),
#             "todate": to_date.strftime("%Y-%m-%d %H:%M")
#         }

#         response = smartapi.getCandleData(params)
#         candles = response['data']
#         df = pd.DataFrame(candles, columns=["datetime", "open", "high", "low", "close", "volume"])
#         df["datetime"] = pd.to_datetime(df["datetime"])
#         return df

#     except Exception as e:
#         print("Error fetching candles:", str(e))
#         return pd.DataFrame()

def get_candle_data(token: List[str], exchange: str, interval: str = "FIVE_MINUTE", days: int = 1, credentials: Dict[str, str] = None):
    try:
        smartapi = get_smartapi_connection(credentials)
        ist = pytz.timezone('Asia/Kolkata')
        to_date = datetime.now(ist)
        from_date = to_date - timedelta(days=days)

        print("🕒 From:", from_date, "To:", to_date)

        instruments = get_instruments_from_openapi(os.getenv("NFO_DATA_URL"), token)
        print("🎯 Tokens fetched:", instruments)

        if not instruments:
            raise ValueError("❌ No instruments returned. Check NFO_DATA_URL or token match.")

        params = {
            "exchange": EXCHANGE_MAP[exchange],
            "symboltoken": instruments[0]['token'],
            "interval": interval, 
            "fromdate": from_date.strftime("%Y-%m-%d %H:%M"),
            "todate": to_date.strftime("%Y-%m-%d %H:%M")
        }

        print("📤 Request Params:", params)

        response = smartapi.getCandleData(params)
        print("📥 Raw response:", response)

        candles = response.get('data')
        if not candles:
            raise ValueError("❗ Empty candle data received")

        df = pd.DataFrame(candles, columns=["datetime", "open", "high", "low", "close", "volume"])
        df["datetime"] = pd.to_datetime(df["datetime"])
        return df

    except Exception as e:
        print("Error fetching candles:", str(e))
        return pd.DataFrame()



class SmartAPIService:
    def __init__(self, smart_client: SmartConnect):
        self.__smart = smart_client

    def get_trade_book(self, order_id):
        max_retries = 3
        delay = 2

        for attempt in range(1, max_retries + 1):
            try:
                logger.info(f"📦 Fetching trade book (Attempt {attempt}) for order ID: {order_id}")
                trade_book = self.__smart.tradeBook()

                if not trade_book or "data" not in trade_book or not trade_book["data"]:
                    logger.warning(f"⚠ Empty or invalid trade book response on attempt {attempt} for order ID: {order_id}")
                else:
                    for trade in trade_book["data"]:
                        if trade.get("orderid") == order_id:
                            logger.info(f"✅ Trade for order {order_id} found in trade book.")
                            return order_id, trade

                logger.warning(f"⚠ Order ID {order_id} not found in trade book on attempt {attempt}.")

            except Exception as e:
                logger.error(f"❌ Exception on fetching trade book attempt {attempt} for order {order_id}: {e}")

            time.sleep(delay)
            delay *= 2

        logger.error(f"❌ Failed to fetch trade info for {order_id} after {max_retries} attempts. Falling back to order book.")
        return self.get_order_book(order_id)

    def get_order_book(self, order_id):
        max_retries = 3
        delay = 2

        for attempt in range(1, max_retries + 1):
            try:
                logger.info(f"📦 Fetching order book (Attempt {attempt}) for order ID: {order_id}")
                order_book = self.__smart.orderBook()

                if not order_book or "data" not in order_book or not order_book["data"]:
                    logger.warning(f"⚠ Empty or invalid order book response on attempt {attempt} for order ID: {order_id}")
                else:
                    for order in order_book["data"]:
                        if order.get("orderid") == order_id:
                            logger.info(f"✅ Order {order_id} found in order book.")
                            return order_id, order

                logger.warning(f"⚠ Order ID {order_id} not found in order book on attempt {attempt}.")

            except Exception as e:
                logger.error(f"❌ Exception on fetching order book attempt {attempt} for order {order_id}: {e}")

            time.sleep(delay)
            delay *= 2

        logger.error(f"❌ Failed to fetch order info for {order_id} after {max_retries} attempts.")
        return order_id, None

    def place_order(self, symbol, token, transaction, ordertype, price, quantity):
        if ordertype == "MARKET":
            price = 0
        try:
            orderparams = {
                "variety": "NORMAL",
                "tradingsymbol": symbol,
                "symboltoken": token,
                "transactiontype": transaction,
                "exchange": "NFO",
                "ordertype": ordertype,
                "producttype": "INTRADAY",
                "duration": "DAY",
                "price": price,
                "squareoff": "0",
                "stoploss": "0",
                "quantity": quantity,
            }

            order_id = self.__smart.placeOrder(orderparams)
            sleep(1)
            logger.info(f"PlaceOrder id : {order_id} ")
            order_id, order_details = self.get_order_book(order_id=order_id)

            if order_details and order_details.get("status") == "rejected":
                logger.error(f"Order {order_id} was rejected: {order_details.get('text', 'Unknown reason')}")
                return order_id, {"status": "rejected", "fillprice": 0, "text": order_details.get("text", "Order rejected")}
            
            return order_id, order_details

        except Exception as e:
            logger.info(f"Order placement failed: {e}")
            return None, {"status": "failed", "fillprice": 0, "text": str(e)}

    def sell_order(self, symbol, token, transaction, ordertype, price, quantity):
        if ordertype == "MARKET":
            price = "0"
        try:
            orderparams = {
                "variety": "NORMAL",
                "tradingsymbol": symbol,
                "symboltoken": token,
                "transactiontype": transaction,
                "exchange": "NFO",
                "ordertype": ordertype,
                "producttype": "INTRADAY",
                "duration": "DAY",
                "price": price,
                "squareoff": "0",
                "stoploss": "0",
                "quantity": quantity,
            }

            order_id = self.__smart.placeOrder(orderparams)
            sleep(1)
            logger.info(f"Sell-order id : {order_id} ")
            order_id, i = self.get_order_book(order_id=order_id)
            return order_id, i

        except Exception as e:
            logger.info(f"Order placement failed: {e}")
            raise ValueError(f"Sell order failed: {e}")


def save_trade(signal_type: str, quantity:int, symbol: str, price: float, token_value: str, user_id: str = None) -> TradeDetails:
    """Save trade details to database - Non-blocking operation"""
    db = None
    try:
        db = SessionLocal()
        
        token_record = get_token_uuid_by_token_value(token_value, db)
        if not token_record:
            logger.error(f"Cannot save trade: Token UUID not found for token value: {token_value}")
            return None

        new_trade = TradeDetails(
            user_id=user_id or "default_user",
            signal=signal_type,
            price=price,
            trade_time=datetime.now(),
            quantity = quantity,
            symbol=symbol,
            name=token_record.name,
            strike_price=token_record.strike,
        )
        
        db.add(new_trade)
        db.commit()
        db.refresh(new_trade)
        
        logger.info(f"✅ Trade saved successfully: {signal_type} at price {price} for token {token_value} (UUID: {token_record.id})")
        return new_trade

    except Exception as e:
        logger.error(f"❌ Error saving trade (non-critical): {e}")
        if db:
            try:
                db.rollback()
            except:
                pass
    finally:
        if db:
            try:
                db.close()
            except:
                pass


def save_trade_record(
                      symbol: str, 
                      quantity:int, 
                      trade_type:str, 
                      user_id: str = None,
                      ltp: float = None,
                      pnl: float = None,
                      order_type: str = None, 
                      strategy_id: str = None) -> TradeDetails:
    """Save trade details to database - Non-blocking operation"""
    db = None
    try:
        db = SessionLocal()
        new_trade = Trade(
            user_id=user_id,
            symbol=symbol,
            quantity=quantity,
            trade_type=trade_type,
            ltp=ltp,
            pnl=pnl,
            order_type=order_type,
            strategy_id=strategy_id,
        )
        
        db.add(new_trade)
        db.commit()
        db.refresh(new_trade)
        
        logger.info(f"✅ Trade saved successfully: {trade_type} at price {ltp} for symbol {symbol}")
        return new_trade

    except Exception as e:
        logger.error(f"❌ Error saving trade (non-critical): {e}")
        if db:
            try:
                db.rollback()
            except:
                pass
    finally:
        if db:
            try:
                db.close()
            except:
                pass


def save_strategy_payload(user_id:str, payload: dict):
  
    db = None
    try:
        db = SessionLocal()
        strategy_payload = StrategyPayload( 
            user_id=user_id,
            strategy_id=payload["strategy_id"],
            index = payload["index"],
            expiry = payload["expiry"],
            strike_price =  payload["strike_price"] * 100,
            option_type = payload["option_type"],
            quantity = payload["quantity"],
            trade_amount = payload["trade_amount"],
            target_profit = payload["target_profit"],
            candle_duration = payload["candle_duration"]
        )
        
        db.add(strategy_payload)
        db.commit()
        db.refresh(strategy_payload)
        
        logger.info(f"✅ payload saved successfully:")
        return strategy_payload

    except Exception as e:
        logger.error(f"❌ Error saving trade (non-critical): {e}")
        if db:
            try:
                db.rollback()
            except:
                pass
    finally:
        if db:
            try:
                db.close()
            except:
                pass