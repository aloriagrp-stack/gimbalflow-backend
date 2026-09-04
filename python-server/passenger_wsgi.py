import os
import sys

# Add the application directory to the Python path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

# Import the FastAPI application
from app.main import app

# cPanel Phusion Passenger runs WSGI.
# a2wsgi bridges ASGI (FastAPI) to WSGI (Passenger) seamlessly.
try:
    from a2wsgi import ASGIMiddleware
    application = ASGIMiddleware(app)
except ImportError:
    # Fallback if a2wsgi isn't installed yet
    def application(environ, start_response):
        status = '200 OK'
        output = b'GimbalFlow backend starting up. Please ensure a2wsgi is installed in requirements.txt.'
        response_headers = [('Content-type', 'text/plain'), ('Content-Length', str(len(output)))]
        start_response(status, response_headers)
        return [output]
