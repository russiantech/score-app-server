import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from asgiref.wsgi import WsgiToAsgi
from main import app   # adjust if our FastAPI file is not main.py

application = WsgiToAsgi(app)
