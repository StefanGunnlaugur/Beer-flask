import os

basedir = os.path.abspath(os.path.dirname(__file__))


class Auth:
    CLIENT_ID = ('650289903160-ajch8e2nn95ro1heod5oide8giothkpi.apps.googleusercontent.com')
    CLIENT_SECRET = 'PGWHtFUXtjYxabbrLnyIw-Xn'
    REDIRECT_URI = 'https://localhost:5000/gCallback'
    AUTH_URI = 'https://accounts.google.com/o/oauth2/auth'
    TOKEN_URI = 'https://accounts.google.com/o/oauth2/token'
    USER_INFO = 'https://www.googleapis.com/userinfo/v2/me'


class Config:
    APP_NAME = "Beer-yo-ass-dev"
    SECRET_KEY = os.environ.get("SECRET_KEY") or "somethingsecret"


class DevConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'postgresql://postgres:password@localhost:5432/flask-beers-dev-db-1")


class ProdConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'postgresql://postgres:password@localhost:5432/flask-beers-dev-db-1")


config = {
    "dev": DevConfig,
    "prod": ProdConfig,
    "default": DevConfig
}