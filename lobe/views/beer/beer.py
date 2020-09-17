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

from lobe.models import (User, db, Beer)
from lobe.db import (resolve_order)
from lobe.forms import (BeerEditForm)

beer = Blueprint(
    'beer', __name__, template_folder='templates')


@beer.route('/beers/')
@login_required
@roles_accepted('admin')
def beer_list():
    beer_list = Beer.query.all()
    #print(beer_list)
    #page = int(request.args.get('page', 1))
    #beer_list = Beer.query.order_by(
    #        resolve_order(
    #            Beer,
    #            request.args.get('sort_by', default='created_at'),
    #            order=request.args.get('order', default='desc')))
        #.paginate(page, per_page=app.config['BEER_PAGINATION'])
    return render_template(
        'beer_list.jinja',
        beer_list=beer_list,
        section='beer')

@beer.route('/beer/<int:id>', methods=['GET', 'POST'])
@login_required
@roles_accepted('admin')
def beer_detail(id):
    beer = Beer.query.get(id)
    return render_template(
        'beer.jinja',
        beer=beer,
        section='beer')


@beer.route('/beer/<int:id>/edit', methods=['POST'])
@login_required
@roles_accepted('admin')
def beer_edit(id):
    try:
        beer = Beer.query.get(id)
        form = BeerEditForm(request.form, obj=instance)
        form.populate_obj(beer)
        db.session.commit()
        response = {}
        return Response(json.dumps(response), status=200)
    except Exception as error:
        app.logger.error('Error creating a verification : {}\n{}'.format(
            error, traceback.format_exc()))
        errorMessage = "<br>".join(list("{}: {}".format(
            key, ", ".join(value)) for key, value in form.errors.items()))
        return Response(errorMessage, status=500)


@beer.route('/beer/post_beer_rating/<int:id>', methods=['POST'])
@login_required
def post_beer_rating(id):
    try:
        beer_id = save_Beer_ratings(request.form, request.files)
    except Exception as error:
        flash(
            "Villa kom upp. Hafið samband við kerfisstjóra",
            category="danger")
        app.logger.error("Error posting rating: {}\n{}".format(
            error, traceback.format_exc()))
        return Response(str(error), status=500)
    if beer_id is None:
        flash("Ekki gekk að senda einkunn", category='warning')
    return url_for('beer_detail', id=id)