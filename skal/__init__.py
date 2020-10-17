"""Initialize Flask app."""
import os
import logging
import json
from logging.handlers import RotatingFileHandler

from flask import Flask, url_for, redirect, \
    render_template, session, request, flash

from flask_reverse_proxy_fix.middleware import ReverseProxyPrefixFix

from flask_login import LoginManager, login_required, login_user, \
    logout_user, current_user, UserMixin

from requests_oauthlib import OAuth2Session
from requests.exceptions import HTTPError

from flask_executor import Executor

from skal.decorators import roles_accepted
from skal.forms import ExtendedLoginForm
from skal.models import User, Role
from skal.models import db as sqlalchemy_db
from skal.filters import format_date

from skal.views.main import main
from skal.views.user import user
from skal.views.beer import beer
from skal.views.beernight import beernight
from skal.views.other import other

os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'



def create_app():
    #user_datastore = SQLAlchemyUserDatastore(sqlalchemy_db, User, Role)
    app = Flask(__name__)
    #app.config.from_object(config['dev'])
    
    if os.getenv('SEMI_PROD', False):
        app.config.from_pyfile('{}.py'.format(os.path.join(
            'settings', 'semi_production')))
    else:
        app.config.from_pyfile('{}.py'.format(os.path.join(
            'settings', os.getenv('FLASK_ENV', 'development'))))
    if 'REVERSE_PROXY_PATH' in app.config:
        ReverseProxyPrefixFix(app)
    app.logger.setLevel(logging.DEBUG)
    app.logger.addHandler(create_logger(app.config['LOG_PATH']))
    app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

    sqlalchemy_db.init_app(app)
    #Security(app, user_datastore)
    # register filters
    app.jinja_env.filters['datetime'] = format_date

    # Propagate background task exceptions
    app.config['EXECUTOR_PROPAGATE_EXCEPTIONS'] = True
    # register blueprints
    app.register_blueprint(main)
    app.register_blueprint(user)
    app.register_blueprint(beer)
    app.register_blueprint(beernight)
    app.register_blueprint(other)


    app.executor = Executor(app)
    #app.user_datastore = user_datastore

    return app


def create_logger(log_path: str):
    logfile_mode = 'w'
    if os.path.exists(log_path):
        logfile_mode = 'a'
    else:
        os.makedirs(os.path.split(log_path)[0])
    handler = RotatingFileHandler(
        log_path,
        maxBytes=1000,
        backupCount=1,
        mode=logfile_mode)
    handler.setLevel(logging.DEBUG)
    handler.setFormatter(logging.Formatter(
        '[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
    ))
    return handler


app = create_app()
'''
@app.after_request
def add_header(response):
    # response.cache_control.no_store = True
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '-1'
    return response
'''
@app.after_request
def add_header(response):
    response.headers['X-UA-Compatible'] = 'IE=Edge,chrome=1'
    if ('Cache-Control' not in response.headers):
        response.headers['Cache-Control'] = 'public, max-age=600'
    return response

#https://bitwiser.in/2015/09/09/add-google-login-in-flask.html
login_manager = LoginManager(app)
login_manager.login_view = "login"
login_manager.session_protection = "strong"

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
""" OAuth Session creation """

@login_manager.unauthorized_handler
def unauthorized():
    # do stuff
    flash("Notanda hefur ekki heimild", category='danger')
    return redirect(url_for('beer.beer_list', drink_type='beer'))