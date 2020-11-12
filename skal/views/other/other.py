import traceback
import imghdr
import secrets
import os
from os import path
from flask import redirect, flash, url_for, request, send_from_directory, render_template, Blueprint
from flask import current_app as app
from flask_login import LoginManager, login_required, login_user, \
    logout_user, current_user, UserMixin

from sqlalchemy import or_
from flask_babel import gettext

from skal.decorators import roles_accepted
from skal.models import User, Role, db, Beer, Beernight, BeernightInvitation
from skal.db import resolve_order, make_beernight, make_beer
from skal.forms import (UserEditForm, ExtendedRegisterForm, RoleForm, BeernightForm,
                        BeerForm)

other = Blueprint(
    'other', __name__, template_folder='templates')


@other.route('/other/beertaste/')
def beer_tasting():
    return render_template(
        'beer_tasting.jinja',
        section='other')


#@other.route('/other/howdrunk/')
#def how_drunk_am_i():
#    return render_template(
#        'how_drunk_am_i.jinja',
#        section='other')

@other.route('/other/howdrunkalpha/')
def how_drunk_alpha():

    return render_template(
        'how_drunk_alpha.jinja',
        section='other')

@other.route('/other/getDub/')
def send_dub():
    filename = 'intense.mp3'
    return send_from_directory(app.config['GAME_AUDIO_DIR'], filename)

@other.route('/other/getEasy/')
def send_easy(): 
    filename = 'easy.mp3'
    return send_from_directory(app.config['GAME_AUDIO_DIR'], filename)