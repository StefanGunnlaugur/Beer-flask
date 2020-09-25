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
from lobe.db import (resolve_order, add_beer_rating, add_beer_comment, 
                    add_beer_favourite, make_beernight, report_comment_db,
                    like_dislike_comment_db, add_beer_to_beernight_db, 
                    delete_beer_from_beernight_db, add_beernight_beer_rating)
from lobe.forms import (BeerEditForm, BeernightForm)

beer = Blueprint(
    'beer', __name__, template_folder='templates')


@beer.route('/beers/')
@login_required
@roles_accepted('admin')
def beer_list():
    beer_list = Beer.query.order_by(
            resolve_order(
                Beer,
                request.args.get('sort_by', default='name'),
                order=request.args.get('order', default='asc'))).all()
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
        comments=comments,
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
        #print(input_comment)
        #print(parent_id)
        if(parent_id):
            comment = add_beer_comment(current_user.id, beer, input_comment, parent_id)
        else:
            comment = add_beer_comment(current_user.id, beer, input_comment)
        return Response(url_for('beer.beer_detail', id=id), status=200)
    except Exception as error:
        flash('Ekki tókst að senda athugasemd',
                    category="warning")
        app.logger.error('Error creating a verification : {}\n{}'.format(
            error, traceback.format_exc()))
        return Response(error, status=500)

@beer.route('/beer/<int:id>/comment/delete/<int:comment_id>')
@login_required
@roles_accepted('admin', 'Notandi')
def delete_comment(id, comment_id):
    try:
        user_id = current_user.id
        comment = BeerComment.query.get(comment_id)
        if user_id == comment.user_id:
            db.session.delete(comment)
            db.session.commit()
        return redirect(url_for('beer.beer_detail', id=id))
    except Exception as error:
        flash('Ekki tókst að eyða athugasemd',
                    category="warning")
        app.logger.error('Error creating a verification : {}\n{}'.format(
            error, traceback.format_exc()))
        return Response(error, status=500)

@beer.route('/beer/comment/report/', methods=['POST'])
@login_required
@roles_accepted('admin', 'Notandi')
def report_comment():
    try:
        user_id = current_user.id
        comment_id = request.form.get('value')
        report = report_comment_db(comment_id, user_id)
        if report:
            flash('Athugasemd hefur verið tilkynnt',
                    category="success")
        response = {}
        return Response(json.dumps(response), status=200)
    except Exception as error:
        flash('Ekki tókst að tilkynna athugasemd',
                    category="warning")
        app.logger.error('Error creating a verification : {}\n{}'.format(
            error, traceback.format_exc()))
        return Response(error, status=500)

@beer.route('/beer/comment/like/', methods=['POST'])
@login_required
@roles_accepted('admin', 'Notandi')
def like_comment():
    try:
        user_id = current_user.id
        comment_id = request.form.get('value')
        like = like_dislike_comment_db(comment_id, user_id)
        return Response(like, status=200)
    except Exception as error:
        flash('Ekki tókst að líka við athugasemd',
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
        rating = add_beer_favourite(current_user, beer, fav_value)
        response = {}
        return Response(json.dumps(response), status=200)
    except Exception as error:
        app.logger.error('Error creating a verification : {}\n{}'.format(
            error, traceback.format_exc()))
        return Response(error, status=500)


@beer.route('/beernight/<int:id>', methods=['GET', 'POST'])
@login_required
@roles_accepted('admin')
def beernight_detail(id):
    user = current_user
    beernight = Beernight.query.get(id)
    rating = beernight.average_rating
    beers = beernight.beers
    return render_template(
        'beernight.jinja',
        beernight=beernight,
        beers=beers,
        rating=rating,
        section='beer')

@beer.route('/beer/<int:id>/add_beer_to_beernight/<int:beernight_id>/')
@login_required
@roles_accepted('admin', 'Notandi')
def add_beer_to_beernight(id, beernight_id):
    try:
        beernight = add_beer_to_beernight_db(id, beernight_id)
        if(beernight):
            flash('Bjór bætt við bjórkvöld',
                    category="success")
        else:
            flash('Ekki tókst að bæta bjór við bjórkvöld',
                    category="warning")
        return redirect(url_for('beer.beer_detail', id=id))
    except Exception as error:
        flash('Ekki tókst að senda athugasemd',
                    category="warning")
        app.logger.error('Error creating a verification : {}\n{}'.format(
            error, traceback.format_exc()))
        return Response(error, status=500)

@beer.route('/beer/<int:id>/delete_beer_from_beernight/<int:beernight_id>')
@login_required
@roles_accepted('admin', 'Notandi')
def delete_beer_from_beernight(id, beernight_id):
    try:
        beernight = delete_beer_from_beernight_db(id)
        if(beernight):
            flash('Bjór var fjarlægður úr bjórkvöldi',
                    category="success")
        else:
            flash('Ekki tókst að fjarlægja bjór úr bjórkvöldi',
                    category="warning")
        return redirect(url_for('beer.beernight_detail', id=beernight_id))
    except Exception as error:
        flash('Ekki tókst að senda athugasemd',
                    category="warning")
        app.logger.error('Error creating a verification : {}\n{}'.format(
            error, traceback.format_exc()))
        return Response(error, status=500)

@beer.route('/beer/beernightbeer/<int:id>/rate', methods=['POST'])
@login_required
@roles_accepted('admin', 'Notandi')
def beernight_beer_rate(id):
    try:
        beer = BeernightBeer.query.get(id)
        input_rating = request.form.get('value')
        input_type = request.form.get('type')
        rating = add_beernight_beer_rating(current_user.id, beer, input_rating, input_type)
        response = {}
        return Response(json.dumps(response), status=200)
    except Exception as error:
        app.logger.error('Error creating a verification : {}\n{}'.format(
            error, traceback.format_exc()))
        return Response(error, status=500)