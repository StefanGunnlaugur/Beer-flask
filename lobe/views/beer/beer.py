import json
import os
import traceback
import random
import numpy as np
from os import path
import imghdr

from zipfile import ZipFile
from operator import itemgetter

from flask import (Blueprint, Response, send_from_directory, request,
                   render_template, flash, redirect, url_for)
from flask import current_app as app
from flask_security import login_required, current_user
from sqlalchemy.exc import IntegrityError

from lobe.decorators import roles_accepted

from lobe.models import (User, db, Beer, BeerRating, BeerComment, CommentLike, CommentReport,
                        Beernight, BeernightBeer, BeernightbeerComment, BeernightbeerRating)
from lobe.db import (resolve_order, add_beer_rating, add_beer_comment, make_beer,
                    add_beer_favourite, make_beernight, report_comment_db,
                    like_dislike_comment_db, add_beer_to_beernight_db, 
                    delete_beer_from_beernight_db, add_beernight_beer_rating)
from lobe.forms import (BeerEditForm, BeernightForm, BeerForm)
from lobe.settings.common import CAT_INDEX, REVERSE_CAT_INDEX

beer = Blueprint(
    'beer', __name__, template_folder='templates')

#@beer.route('/<string:drink_type>/')

@beer.route('/list/<string:drink_type>/')
def beer_list(drink_type):
    #filter_var = drink_type
    filter_name = 'Bjór'
    if drink_type in CAT_INDEX:
        filter_name = CAT_INDEX[drink_type]
    else:
        drink_type = 'beer'

    if request.args.get('sort_by') == 'book_score':
        beer_list = Beer.query.filter(Beer.category == filter_name).all()
        reverse=True
        if request.args.get('order') == 'asc':
            reverse = False
        beer_list = sorted(beer_list, key=lambda x: x.calculateBook, reverse=reverse)
    elif request.args.get('sort_by') == 'rating':
        beer_list = Beer.query.filter(Beer.category == filter_name).all()
        reverse=True
        if request.args.get('order') == 'asc':
            reverse = False
        beer_list = sorted(beer_list, key=lambda x: x.float_average_rating, reverse=reverse)
    elif request.args.get('sort_by') == 'economic_score':
        beer_list = Beer.query.filter(Beer.category == filter_name).all()
        reverse=True
        if request.args.get('order') == 'asc':
            reverse = False
        beer_list = sorted(beer_list, key=lambda x: x.bang_for_buck, reverse=reverse)
    else:
        beer_list = Beer.query.filter(Beer.category == filter_name).order_by(
                resolve_order(
                    Beer,
                    request.args.get('sort_by', default='name'),
                    order=request.args.get('order', default='asc'))).all()
    
    cats = []
    for b in beer_list:
        if b.beer_type and not b.beer_type in cats:
            if b.beer_type == '':
                pass
            else:
                cats.append(b.beer_type)
    return render_template(
        'beer_list.jinja',
        cat_name=CAT_INDEX[drink_type],
        beer_list=beer_list,
        categories=cats,
        section=drink_type)

@beer.route('/beer/<int:id>', methods=['GET', 'POST'])
@login_required
@roles_accepted(['admin', 'Notandi'])
def beer_detail(id):
    user = current_user
    beer = Beer.query.get(id)
    comments = BeerComment.query\
        .filter(BeerComment.beer_id == id) \
        .filter(BeerComment.parent_comment_id == None).order_by(
            resolve_order(
                BeerComment,
                request.args.get('sort_by', default='created_at'),
                order=request.args.get('order', default='desc'))).all()
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
                        "Ekki tókst að búa til bjórkvöld.",
                        category="warning")
            except Exception as error:
                print(error)
                flash(
                    "Ekki tókst að búa til bjórkvöld.",
                    category="warning")
        else:
            flash(
                "Ekki tókst að búa til bjórkvöld.",
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
        section=REVERSE_CAT_INDEX[beer.category])

@beer.route('/beer/sendImage/<int:id>/')
def send_beer_image(id):
    beer = Beer.query.get(id)
    try:
        if beer.image_path:
            if path.exists(os.path.join(app.config['BEERS_IMAGE_DIR'], beer.image_path)):
                return send_from_directory(
                    app.config['BEERS_IMAGE_DIR'],
                    beer.image_path)
        return send_from_directory(
            app.config['STATIC_DATA_DIR'],
            'defaultBeerImage.png')
    except Exception as error:
        app.logger.error(
            "Error sending a beernight image : {}\n{}".format(
                error, traceback.format_exc()))
    return ''

@beer.route('/beer/<int:id>/comment', methods=['POST'])
@login_required
@roles_accepted(['admin', 'Notandi'])
def beer_comment(id):
    try:
        beer = Beer.query.get(id)
        input_comment = request.form.get('text')
        parent_id = request.form.get('parent')
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
@roles_accepted(['admin', 'Notandi'])
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

@beer.route('/beer/comment/<int:id>/report/')
@login_required
@roles_accepted(['admin', 'Notandi'])
def report_comment(id):
    try:
        user_id = current_user.id
        comment_id = id
        comment = BeerComment.query.get(comment_id)
        report = report_comment_db(comment_id, user_id)
        if report:
            flash('Athugasemd hefur verið tilkynnt',
                    category="success")
        
        return redirect(url_for('beer.beer_detail', id=comment.beer_id))
    except Exception as error:
        flash('Ekki tókst að tilkynna athugasemd',
                    category="warning")
        app.logger.error('Error creating a verification : {}\n{}'.format(
            error, traceback.format_exc()))
        return redirect(url_for('beer.beer_detail', id=id))

@beer.route('/beer/comment/like/', methods=['POST'])
@login_required
@roles_accepted(['admin', 'Notandi'])
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
@roles_accepted(['admin', 'Notandi'])
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
@roles_accepted(['admin', 'Notandi'])
def beer_favourite(id):
    try:
        beer = Beer.query.get(id)
        fav_value = request.form.get('value')
        rating = add_beer_favourite(current_user, beer, fav_value)
        response = {"res": str(rating)}
        return Response(json.dumps(response), status=200)
    except Exception as error:
        app.logger.error('Error creating a verification : {}\n{}'.format(
            error, traceback.format_exc()))
        return Response(error, status=500)

@beer.route("/beer/make/", methods=['POST'])
@login_required
@roles_accepted(['admin'])
def make_beer_route():
    form = BeerForm(request.form)
    if form.validate():
        try:
            image_file = request.files['picture']
            if image_file.filename != '':
                if imghdr.what(image_file) in ['jpg', 'png', 'gif', 'jpeg']:
                    beer = make_beer(form, image_file)
                    if beer:
                        flash("Tókst að búa til bjór {}.".format(
                                    beer.name),
                                    category="success")
                        return redirect(url_for('beer.beer_detail', id=id))
                    else:
                        flash(
                            "Ekki tókst að búa til bjór.",
                            category="warning")
                else:
                    flash(
                        "Ekki tókst að búa til bjór. Mynd ekki á réttur formi",
                        category="warning")
            else:
                flash(
                    "Ekki tókst að búa til bjór. Mynd vantar.",
                    category="warning")
        except Exception as error:
            print(error)
            flash(
                "Ekki tókst að búa til bjór.",
                category="warning")
    else:
        flash(
            "Ekki var fyllt rétt inn í reiti!",
            category="warning")
    return redirect(url_for('user.admin_page'))
    

@beer.route('/beer/<int:id>/delete')
@login_required
@roles_accepted(['admin'])
def beer_delete(id):
    try:
        beer = Beer.query.get(id)
        db.session.delete(beer)
        db.session.commit()
        if beer.image_path:
            if path.exists(os.path.join(app.config['BEERS_IMAGE_DIR'], beer.image_path)):
                os.remove(os.path.join(app.config['BEERS_IMAGE_DIR'], beer.image_path))
        flash('Bjór {} hefur verið eytt'.format(beer.name), category="success")
        return redirect(url_for('beer.beer_list', drink_type='beer'))
    except Exception as error:
        flash('Ekki tókst að eyða bjór',
                    category="warning")
        app.logger.error('Error creating a verification : {}\n{}'.format(
            error, traceback.format_exc()))
        return redirect(url_for('beer.beer_list', drink_type='beer'))



