import sys
import uvicorn
from pathlib import Path

# Add current directory to python path
ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.config.settings import settings

if __name__ == "__main__":
    print(f"Starting GimbalFlow Unified FastAPI Server on {settings.HOST}:{settings.PORT} ...")
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=True)
