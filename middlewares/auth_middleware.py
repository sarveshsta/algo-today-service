from fastapi import Header, HTTPException
from cryptography.fernet import Fernet
import json

FERNET_KEY = "rY2gXxHdqqEEqo7Ff2h4R_4ckzwnaioMhs5OOAyYsOU="
fernet = Fernet(FERNET_KEY.encode())

def decrypt_encrypted_token(encrypted_token: str):
    try:
        decrypted_payload = fernet.decrypt(encrypted_token.encode()).decode()
        return json.loads(decrypted_payload)
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Token decryption failed: {str(e)}")


def verify_token(Authorization: str = Header(...)):
    try:
        # No 'Bearer ' prefix — assume raw token
        return decrypt_encrypted_token(Authorization)
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Token decryption failed: {str(e)}")
