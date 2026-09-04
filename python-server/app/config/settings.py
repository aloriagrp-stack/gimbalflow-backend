import os
from pathlib import Path
from dotenv import load_dotenv

# Locate and load .env file
CURRENT_DIR = Path(__file__).resolve().parent
APP_DIR = CURRENT_DIR.parent
SERVER_DIR = APP_DIR.parent

env_paths = [
    SERVER_DIR / ".env",
    APP_DIR / ".env",
    SERVER_DIR.parent / "node-server" / ".env"
]

for env_path in env_paths:
    if env_path.exists():
        load_dotenv(dotenv_path=env_path)
        break

class Settings:
    PORT: int = int(os.getenv("PORT", "5000"))
    HOST: str = os.getenv("HOST", "0.0.0.0")

    # MySQL
    MYSQL_HOST: str = os.getenv("MYSQL_HOST", "localhost")
    MYSQL_PORT: int = int(os.getenv("MYSQL_PORT", "3306"))
    MYSQL_USER: str = os.getenv("MYSQL_USER", "root")
    MYSQL_PASSWORD: str = os.getenv("MYSQL_PASSWORD", "")
    MYSQL_DATABASE: str = os.getenv("MYSQL_DATABASE", "gimbalflow_db")

    # Redis
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))

    # Admin Credentials
    ADMIN_USERNAME: str = os.getenv("ADMIN_USERNAME", "shriyanshaloria")
    ADMIN_PASSWORD_HASH: str = os.getenv("ADMIN_PASSWORD_HASH", "")
    ADMIN_TOKEN_TTL_HOURS: int = int(os.getenv("ADMIN_TOKEN_TTL_HOURS", "12"))

    # Firebase Web API Key for Google Token Verification
    FIREBASE_API_KEY: str = os.getenv("FIREBASE_API_KEY", "AIzaSyCooVb9tdiuGBkqAsJlue4MWsO2B6bUrow")

    # Directories
    BASE_DIR: Path = SERVER_DIR
    DATA_DIR: Path = SERVER_DIR / "data"
    UPLOADS_DIR: Path = SERVER_DIR / "uploads"
    HERO_UPLOADS_DIR: Path = UPLOADS_DIR / "hero"

settings = Settings()

# Ensure directories exist
settings.DATA_DIR.mkdir(parents=True, exist_ok=True)
settings.HERO_UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
