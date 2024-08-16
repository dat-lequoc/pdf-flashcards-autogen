from flask import Flask
from config import Config
from utils import get_recent_pdfs

app = Flask(__name__)
app.config.from_object(Config)

from routes import *

if __name__ == '__main__':
    app.run(debug=True)
