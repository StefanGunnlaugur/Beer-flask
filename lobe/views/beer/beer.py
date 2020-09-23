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

from lobe.models import (User, db, Beer, BeerRating, BeerComment)
from lobe.db import (resolve_order, add_beer_rating, add_beer_comment, 
                    add_beer_favourite, make_beernight)
from lobe.forms import (BeerEditForm, BeernightForm)

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
    user = current_user
    beer = Beer.query.get(id)
    comments = BeerComment.query\
        .filter(BeerComment.beer_id == id) \
        .filter(BeerComment.parent_comment_id == None).all()
    print(comments)
    form = BeernightForm(request.form)
    if request.method == 'POST':
        if form.validate():
            try:
                beernight = make_beernight(form, beer, user)
                if beernight:
                    flash("Tókst að búa til bjórkvöld {}.".format(
                                beernight.name),
                                category="success")
                else:
                    flash(
                        "Ekki tókst að hlaða búa til bjórkvöld.",
                        category="warning")
            except Exception as error:
                print(error)
                flash(
                    "Ekki tókst að hlaða búa til bjórkvöld.",
                    category="warning")
        else:
            flash(
                "Ekki tókst að hlaða búa til bjórkvöld.",
                category="warning")
        return redirect(url_for('beer.beer_detail', id=id))

    rating = 'null'
    liked = 'null'
    if user:
        beer_ratings = BeerRating.query\
        .filter(BeerRating.beer_id == beer.id) \
        .filter(BeerRating.user_id == user.id).first()
        if beer_ratings:
            rating = beer_ratings.rating
        liked_beers = user.beers
        for i in liked_beers:
            if i.id == id:
                liked = 'true'
    return render_template(
        'beer.jinja',
        beer=beer,
        rating=rating,
        liked=liked,
        beernight_form = form,
        section='beer')


@beer.route('/beer/<int:id>/comment', methods=['POST'])
@login_required
@roles_accepted('admin', 'Notandi')
def beer_comment(id):
    try:
        beer = Beer.query.get(id)
        input_comment = request.form.get('text')
        parent_id = request.form.get('parent')
        if(parent_id):
            comment = add_beer_comment(current_user.id, beer, input_comment, parent_id)
        else:
            comment = add_beer_comment(current_user.id, beer, input_comment)
        print(url_for('beer.beer_detail', id=id))
        return Response(url_for('beer.beer_detail', id=id), status=200)
    except Exception as error:
        flash('Ekki tókst að senda athugasemd',
                    category="warning")
        app.logger.error('Error creating a verification : {}\n{}'.format(
            error, traceback.format_exc()))
        return Response(error, status=500)

@beer.route('/beer/<int:id>/rate', methods=['POST'])
@login_required
@roles_accepted('admin', 'Notandi')
def beer_rate(id):
    try:
        beer = Beer.query.get(id)
        input_rating = request.form.get('value')
        rating = add_beer_rating(current_user.id, beer, input_rating)
        response = {}
        return Response(json.dumps(response), status=200)
    except Exception as error:
        app.logger.error('Error creating a verification : {}\n{}'.format(
            error, traceback.format_exc()))
        return Response(error, status=500)

@beer.route('/beer/<int:id>/favourite', methods=['POST'])
@login_required
@roles_accepted('admin', 'Notandi')
def beer_favourite(id):
    try:
        beer = Beer.query.get(id)
        fav_value = request.form.get('value')
        print(fav_value)
        rating = add_beer_favourite(current_user, beer, fav_value)
        response = {}
        return Response(json.dumps(response), status=200)
    except Exception as error:
        app.logger.error('Error creating a verification : {}\n{}'.format(
            error, traceback.format_exc()))
        return Response(error, status=500)

