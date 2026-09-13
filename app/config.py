import os

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///./vulntracker.db",
)

SECRET_KEY = os.getenv("SECRET_KEY")

if not SECRET_KEY:
    raise RuntimeError("SECRET_KEY environment variable is required")

ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(
    os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30")
)

DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
ADMIN_API_KEY = os.getenv("ADMIN_API_KEY")

NOTIFY_SERVICE_URL = os.getenv(
    "NOTIFY_SERVICE_URL",
    "http://localhost:3001",
)