import os

APP_ROOT = os.path.abspath(os.path.join(
    os.path.dirname(os.path.abspath(__file__)), os.pardir))


# Path to the logging file
LOG_PATH = os.path.join(APP_ROOT, os.pardir, 'logs', 'info.log')

# For other static files, like the LOBE manual
OTHER_DIR = os.path.join(APP_ROOT, os.pardir, 'other')

BEER_PAGINATION = 500
USER_PAGINATION = 10


SESSION_SZ = 50

RECAPTCHA_USE_SSL = False
RECAPTCHA_DATA_ATTRS = {'theme': 'dark'}

SQLALCHEMY_TRACK_MODIFICATIONS = False

SECURITY_LOGIN_USER_TEMPLATE = 'login_user.jinja'

# The default configuration id stored in database
DEFAULT_CONFIGURATION_ID = 1

COLORS = {
    'common': "#bdbdbd",
    'rare': "#42a5f5",
    'epic': "#7e57c2",
    'legendary': "#ffc107",
    'danger': "#ff4444",
    'primary': "#0275d8",
    'success': "#5cb85c",
    'info': "#5bc0de",
    'warning': "#f0ad4e",
    'diamond': "#ff4444",
}


