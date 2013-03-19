import sys
import os
import logging

from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['DATABASE_URL']
app.debug = os.environ.get('DEBUG', False)
db = SQLAlchemy(app)

# Import all the views for the app
from thirdpanel.views import *

if __name__ == '__main__':
    logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

    # Bind to PORT if defined, otherwise default to 5000.
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
