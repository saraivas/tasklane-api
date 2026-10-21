from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
from passlib.context import CryptContext
from app.core.config import (
  SECRET_KEY,
  ALGORITHM,
  ACCESS_TOKEN_EXPIRE_MINUTES,
  REFRESH_TOKEN_EXPIRE_DAYS,
  SESSION_MAX_LIFETIME_DAYS,
)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
  return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
  return pwd_context.verify(plain_password, hashed_password)


def create_access_token(user_id: str) -> str:
  expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
  payload = {"sub": user_id, "exp": expire, "type": "access"}
  return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def session_expires_at(auth_time: int) -> datetime:
  """When the session that started at `auth_time` (unix seconds) must end."""
  started = datetime.fromtimestamp(auth_time, tz=timezone.utc)
  return started + timedelta(days=SESSION_MAX_LIFETIME_DAYS)


def session_has_expired(auth_time: int) -> bool:
  return datetime.now(timezone.utc) >= session_expires_at(auth_time)


def create_refresh_token(user_id: str, auth_time: int | None = None) -> str:
  """Issue a refresh token.

  `auth_time` is the unix time of the original login. It is set at login and
  carried unchanged through every refresh. The token's own expiry slides
  (a fresh REFRESH_TOKEN_EXPIRE_DAYS window each time), but never goes past
  auth_time + SESSION_MAX_LIFETIME_DAYS.
  """
  now = datetime.now(timezone.utc)
  if auth_time is None:
    auth_time = int(now.timestamp())
  expire = min(
    now + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
    session_expires_at(auth_time),
  )
  payload = {
    "sub": user_id,
    "exp": expire,
    "iat": now,
    "auth_time": auth_time,
    "type": "refresh",
  }
  return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> dict | None:
  try:
      payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
      return payload
  except JWTError:
      return None
