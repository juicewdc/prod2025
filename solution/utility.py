from datetime import datetime, timedelta, timezone
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from cfg import pwd_context, secret_key, alg

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=30)
    to_encode.update({
        "exp": expire,
        "iat": int(datetime.now(timezone.utc).timestamp())
    })
    encoded_jwt = jwt.encode(to_encode, secret_key, algorithm=alg)
    return encoded_jwt

security = HTTPBearer()


def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, secret_key, algorithms=[alg])
        print("Decoded payload:", payload)
        return payload
    except JWTError as e:
        print("Token decoding error:", e)
        raise HTTPException(status_code=401, detail="Неверный токен")

