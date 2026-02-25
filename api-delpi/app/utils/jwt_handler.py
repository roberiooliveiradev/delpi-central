# app/utils/jwt_handler.py
import jwt
from datetime import datetime, timedelta
from app.config import settings

SECRET_KEY = settings.JWT_SECRET
ALGORITHM = "HS256"
EXPIRATION_MINUTES = 60

def create_token(data: dict) -> str:
    to_encode = data.copy()
    to_encode.update({"exp": datetime.utcnow() + timedelta(minutes=EXPIRATION_MINUTES)})
    token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return token

def verify_token(token: str) -> dict:
    try:
        decoded = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return decoded
    except jwt.ExpiredSignatureError:
        raise ValueError("Token expirado")
    except jwt.InvalidTokenError:
        raise ValueError("Token inválido")
