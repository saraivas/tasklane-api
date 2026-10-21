# app/core/config.py
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))
# Each refresh token is valid for this many days from the moment it is issued.
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", 7))
# Hard ceiling on a session, counted from the original login, no matter how
# often the refresh token is renewed. See docs/adr/0010.
SESSION_MAX_LIFETIME_DAYS = int(os.getenv("SESSION_MAX_LIFETIME_DAYS", 30))
