import os
import traceback
import json
from os import path
from flask import (redirect, url_for, render_template, send_from_directory,
                   flash, request, Blueprint, session)
from flask_babel import gettext
from flask import current_app as app
from flask_security import current_user, login_required
from skal.decorators import roles_accepted

from skal.models import User, Role, db
from flask import current_app as app
from flask_login import LoginManager, login_required, login_user, \
    logout_user, current_user, UserMixin
from requests_oauthlib import OAuth2Session
from requests.exceptions import HTTPError
from flask_babel import Babel

main = Blueprint(
    'main', __name__,
    template_folder='templates',
    static_folder='static',
    static_url_path='/main/static')


@main.route('/')
def index():
    if not current_user.is_anonymous:
        return redirect(url_for('user.current_user_detail'))
    return redirect(url_for('beer.beer_list', drink_type='beer'))


@main.errorhandler(404)
def page_not_found(error):
    flash(gettext("Við fundum ekki síðuna sem þú baðst um."), category="warning")
    return redirect(url_for('index'))


@main.errorhandler(500)
def internal_server_error(error):
    flash(gettext("Alvarleg villa kom upp, vinsamlega reynið aftur"), category="danger")
    app.logger.error('Server Error: %s', (error))
    return redirect(url_for('index'))


@main.route('/not-in-chrome/')
def not_in_chrome():
    return render_template(
        'not_in_chrome.jinja',
        previous=request.args.get('previous'))


#Login handle
class Auth:
    CLIENT_ID = ('650289903160-ajch8e2nn95ro1heod5oide8giothkpi.apps.googleusercontent.com')
    CLIENT_SECRET = 'PGWHtFUXtjYxabbrLnyIw-Xn'
    REDIRECT_URI = os.environ.get('CALLBACK_URI')
    AUTH_URI = 'https://accounts.google.com/o/oauth2/auth'
    TOKEN_URI = 'https://accounts.google.com/o/oauth2/token'
    USER_INFO = 'https://www.googleapis.com/userinfo/v2/me'
    SCOPE = ['profile', 'email']



class Config:
    APP_NAME = "Beer-yo-ass-dev"
    SECRET_KEY = os.environ.get("SECRET_KEY") or "somethingsecret"



def get_google_auth(state=None, token=None):
    if token:
        return OAuth2Session(Auth.CLIENT_ID, token=token)
    if state:
        return OAuth2Session(
            Auth.CLIENT_ID,
            state=state,
            redirect_uri=Auth.REDIRECT_URI)
    oauth = OAuth2Session(
        Auth.CLIENT_ID,
        redirect_uri=Auth.REDIRECT_URI,
        scope=Auth.SCOPE)
    return oauth

@main.route('/login')
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    google = get_google_auth()
    auth_url, state = google.authorization_url(
        Auth.AUTH_URI, access_type='offline')
    session['oauth_state'] = state
    return render_template('login_user.jinja', auth_url=auth_url)

def create_directories(user_id):
    if not path.exists(os.path.join(app.config['USERS_DATA_DIR'], str(user_id))):
        user_path = os.path.join(app.config['USERS_DATA_DIR'], str(user_id))
        os.mkdir(user_path)
        os.mkdir(os.path.join(user_path, "beernights"))
        os.mkdir(os.path.join(user_path, "other"))


@main.route('/gCallback')
def callback():
    if current_user is not None and current_user.is_authenticated:
        return redirect(url_for('main.index'))
    if 'error' in request.args:
        if request.args.get('error') == 'access_denied':
            return 'You denied access.'
        return 'Error encountered.'
    if 'code' not in request.args and 'state' not in request.args:
        return redirect(url_for('login'))
    else:
        google = get_google_auth(state=session['oauth_state'])
        try:
            token = google.fetch_token(
                Auth.TOKEN_URI,
                client_secret=Auth.CLIENT_SECRET,
                authorization_response=request.url)
        except HTTPError:
            return 'HTTPError occurred.'
        google = get_google_auth(token=token)
        resp = google.get(Auth.USER_INFO)
        if resp.status_code == 200:
            user_data = resp.json()
            email = user_data['email']
            user = User.query.filter_by(email=email).first()
            if user is None:
                role = Role.query.filter(Role.name == 'Notandi').first()
                user = User()
                user.email = email
                user.active = True
                user.roles.append(role)
                db.session.flush()
                create_directories(user.id)
            user.name = user_data['name']
            user.tokens = json.dumps(token)
            user.avatar = user_data['picture']
            db.session.add(user)
            db.session.commit()
            if not user.active:
                flash(gettext("{} er óvirkur notandi, hafðu samband við kerfisstjóra".format(user.name)), category='warning')
            log = login_user(user)
            return redirect(url_for('main.index'))
        return 'Could not fetch your information.'


@main.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('beer.beer_list', drink_type='beer'))

@main.route('/language/<language>')
def set_language(language=None):
    session['language'] = language
    return redirect(request.referrer)

@main.route('/get_flag_icon/<flag>')
def get_flag_icon(flag):
    if flag in app.config['LANGUAGES']:
        try:
            name=flag+'.png'
            if path.exists(os.path.join(app.config['ICON_DIR'], name)):
                return send_from_directory(
                    app.config['ICON_DIR'],
                    name)
        except Exception as error:
            app.logger.error(
                "Error sending a beernight image : {}\n{}".format(
                    error, traceback.format_exc()))
    return ''