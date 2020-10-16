import traceback
import imghdr
import secrets
import os
from os import path
from flask import redirect, flash, url_for, request, render_template, Blueprint
from flask import current_app as app
from flask_login import LoginManager, login_required, login_user, \
    logout_user, current_user, UserMixin

from sqlalchemy import or_

from lobe.decorators import roles_accepted
from lobe.models import User, Role, db, Beer, Beernight, BeernightInvitation
from lobe.db import resolve_order, make_beernight, make_beer
from lobe.forms import (UserEditForm, ExtendedRegisterForm, RoleForm, BeernightForm,
                        BeerForm)

other = Blueprint(
    'other', __name__, template_folder='templates')


@other.route('/other/beertaste/')
def beer_tasting():
    return render_template(
        'beer_tasting.jinja',
        section='other')


@other.route('/other/howdrunk/')
def how_drunk_am_i():
    return render_template(
        'how_drunk_am_i.jinja',
        section='other')

@other.route('/other/howdrunkalpha/')
def how_drunk_alpha():

    return render_template(
        'how_drunk_alpha.jinja',
        user=user,
        section='other')

@other.route('/other/getDub/')
def getDub():

    return send_from_directory('/home/name/Music/', filename)

