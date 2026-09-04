import os
import sys

# Add root and python-server to sys.path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PYTHON_SERVER_DIR = os.path.join(CURRENT_DIR, "python-server")

for p in [PYTHON_SERVER_DIR, CURRENT_DIR]:
    if p not in sys.path:
        sys.path.insert(0, p)

from app.main import app

try:
    from a2wsgi import ASGIMiddleware
    application = ASGIMiddleware(app)
except ImportError:
    def application(environ, start_response):
        status = '200 OK'
        output = b'GimbalFlow backend starting. Please install a2wsgi via pip.'
        response_headers = [('Content-type', 'text/plain'), ('Content-Length', str(len(output)))]
        start_response(status, response_headers)
        return [output]
