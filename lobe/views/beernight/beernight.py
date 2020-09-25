import json
import traceback
import random
import numpy as np
from zipfile import ZipFile
from operator import itemgetter

from flask import (Blueprint, Response, send_from_directory, request,
                   render_template, flash, redirect, url_for)
from flask import current_app as app
from flask_security import login_required, roles_accepted, current_user
from sqlalchemy.exc import IntegrityError

from lobe.models import (User, db, Beer, BeerRating, BeerComment, CommentLike, CommentReport,
                        Beernight, BeernightBeer, BeernightbeerComment, BeernightbeerRating)
from lobe.forms import (BeerEditForm, BeernightForm)

beernight = Blueprint(
    'beernight', __name__, template_folder='templates')


@beernight.route('/beernights/')
def public_beernights():
    beernights = Beernight.query\
            .filter(Beernight.is_public == True)
    return render_template(
        'public_beernights.jinja',
        beernights = beernights,
        section='beernight')