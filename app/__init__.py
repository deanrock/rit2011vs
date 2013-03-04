from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy

import os
from flask.ext.login import LoginManager
from flask.ext.openid import OpenID
from config import basedir
from flaskext.babel import Babel, format_datetime


app = Flask(__name__)
app.config.from_object('config')
db = SQLAlchemy(app)
babel = Babel(app)
lm = LoginManager()
lm.setup_app(app)
lm.login_view = 'login_oid'
oid = OpenID(app, os.path.join(basedir, 'tmp'))


from app import views, models