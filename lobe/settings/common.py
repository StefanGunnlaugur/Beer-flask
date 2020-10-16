import os

APP_ROOT = os.path.abspath(os.path.join(
    os.path.dirname(os.path.abspath(__file__)), os.pardir))


# Path to the logging file
LOG_PATH = os.path.join(APP_ROOT, os.pardir, 'logs', 'info.log')

# For other static files, like the LOBE manual
DATA_BASE_DIR = os.path.join(APP_ROOT, os.pardir, 'data/')
IMAGE_DIR = os.path.join(DATA_BASE_DIR, 'images/')
BEERNIGHT_IMAGE_DIR = os.path.join(IMAGE_DIR, 'beernights/')
BEERS_IMAGE_DIR = os.path.join(IMAGE_DIR, 'beers/')
USERS_DATA_DIR = os.path.join(IMAGE_DIR, 'users/')
STATIC_DATA_DIR = os.path.join(IMAGE_DIR, 'static/')
OTHER_DIR = os.path.join(APP_ROOT, os.pardir, 'other')

BEER_PAGINATION = 500
USER_PAGINATION = 10
USER_TABLES_PAGINATION = 15



SESSION_SZ = 50

RECAPTCHA_USE_SSL = False
RECAPTCHA_DATA_ATTRS = {'theme': 'dark'}

SQLALCHEMY_TRACK_MODIFICATIONS = False

#SECURITY_LOGIN_USER_TEMPLATE = 'login_user.jinja'

# The default configuration id stored in database
DEFAULT_CONFIGURATION_ID = 1

CAT_INDEX = {'beer': 'Bjór', 'red': 'Rauðvín', 'white':'Hvítvín', 'spirits':'Sterkt', 'rose':'Rósavín', 'bubble':'Freyðivín', 'sider':'Síder og blöndur', 'desert':'Eftirréttavín o.fl.', 'other':'Annað'}
CAT_INDEX = {'beer': 'Bjór', 'red': 'Rauðvín', 'white':'Hvítvín', 'spirits':'Sterkt', 'rose':'Rósavín', 'bubble':'Freyðivín', 'sider':'Síder og blöndur', 'desert':'Eftirréttavín o.fl.', 'other':'Annað'}
REVERSE_CAT_INDEX = {'Bjór': 'beer', 'Rauðvín': 'red', 'Hvítvín':'white', 'Sterkt':'spirits', 'Rósavín':'rose', 'Freyðivín':'bubble', 'Síder og blöndur':'sider', 'Eftirréttavín o.fl.':'desert', 'Annað':'other'}

#DRINK_CATEGORIES = ['Bjór', 'Rauðvín', 'Hvítvín', 'Sterkt', 'Rósavín', 'Freyðivín', 'Síder og blöndur', 'Eftirréttavín o.fl.', 'Annað']

COLORS = {
    'common': "#bdbdbd",
    'rare': "#42a5f5",
    'epic': "#7e57c2",
    'legendary': "#ffc107",
    'nice': "#56c256",
    'perfect': "#c25656",
    'danger': "#ff4444",
    'primary': "#0275d8",
    'success': "#5cb85c",
    'info': "#5bc0de",
    'white': "#ffffff",
    'warning': "#f0ad4e",
    'warningDark': '#d38312',
    'diamond': "#ff4444",
    'darkGrey': "#737373",
    'siteBackgroundDark': '#46344e',
    'siteBackground': '#f1f1f1',
    'headerColor': '#f0ad4e',
    'redWine':'#ef4d4d',
    'whiteWine':'#dbf47c',
    'spirits':'#E38200',
    'headerFadedColor': '#f9deb9',
    'fontColor': '#000000',
    'lineColor': '#ffffff',
    'fourthColor': '#9b786f',
    'publicBeernightColor': '#8b9c8b',
    'publicHover': '#6f9b6f',
    'navSelected': '#6f9b6f',

    'adminColor': '#7474b4',
    'adminHover': '#5959a6',
    'memberColor': '#b47474',
    'memberHover': '#a65959',
    'inviteColor': '#9c9c8b',
    'inviteHover': '#8a8a75',

    'heartChecked': '#cc0000',
    'heartUnChecked': '#6b6161',
}


