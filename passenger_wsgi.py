# GimbalFlow Backend - cPanel WSGI Entry Point
# Deployment sync verified with SSH Deploy Key
import os
import sys
import importlib

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PYTHON_SERVER_DIR = os.path.join(CURRENT_DIR, "python-server")

for path in [CURRENT_DIR, PYTHON_SERVER_DIR]:
    if os.path.exists(path) and path not in sys.path:
        sys.path.insert(0, path)

# Dynamically resolve and import the FastAPI app
app = None
try:
    from app.main import app as fastapi_app
    app = fastapi_app
except ImportError:
    try:
        app_mod = importlib.import_module("app.main")
        app = getattr(app_mod, "app")
    except Exception as e:
        print("[passenger_wsgi] Error loading FastAPI app:", e)

# Bridge ASGI (FastAPI) to WSGI for cPanel Phusion Passenger
try:
    from a2wsgi import ASGIMiddleware
    if app is not None:
        application = ASGIMiddleware(app)
    else:
        raise RuntimeError("FastAPI app instance is None")
except Exception as err:
    # Safe fallback if dependencies are still being installed on cPanel
    def application(environ, start_response):
        status = '200 OK'
        msg = f"GimbalFlow backend initializing. Status: {err}\nPlease run 'pip install -r requirements.txt' in cPanel."
        output = msg.encode("utf-8")
        response_headers = [
            ('Content-Type', 'text/plain; charset=utf-8'),
            ('Content-Length', str(len(output)))
        ]
        start_response(status, response_headers)
        return [output]
