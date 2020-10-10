import json
import traceback
import random
import numpy as np
from datetime import date
from zipfile import ZipFile
from operator import itemgetter

import flask_excel as excel
from flask import (Blueprint, Response, send_from_directory, request,
                   render_template, flash, redirect, url_for)
from flask import current_app as app
from flask_security import login_required, current_user
from sqlalchemy.exc import IntegrityError
import random
from lobe.decorators import roles_accepted, member_of_beernight
from lobe.models import (User, db, Beer, BeerRating, BeerComment, CommentLike, CommentReport,
                        Beernight, BeernightBeer, BeernightbeerComment, BeernightbeerRating)
from lobe.db import (resolve_order, add_beer_rating, add_beer_comment, 
                    add_beer_favourite, make_beernight, report_comment_db,
                    like_dislike_comment_db, add_beer_to_beernight_db, 
                    delete_beer_from_beernight_db, add_beernight_beer_rating,
                    send_beernight_invitation_db, accept_beernight_invitation_db,
                    delete_beernight_invitation_db, copy_public_beernight,
                    add_beernight_rating, make_member_admin, remove_member_from_beernight,
                    make_beernightbeer)
from lobe.forms import (BeerEditForm, BeernightForm, CopyBeernightForm, BeernightbeerForm)

beernight = Blueprint(
    'beernight', __name__, template_folder='templates')


@beernight.route('/beernights/')
def public_beernights():
    beernights = Beernight.query\
            .filter(Beernight.is_public == True)
    beernights_sorted = sorted(beernights, key=lambda x: x.name, reverse=False)
    beernights_sorted = beernights_sorted + beernights_sorted + beernights_sorted + beernights_sorted + beernights_sorted
    featured_beernights = Beernight.query.filter(Beernight.is_featured == True)
    
    high_rated_beernights = sorted(beernights, key=lambda x: x.float_average_rating, reverse=False)
    most_copied_beernights = sorted(beernights, key=lambda x: x.get_copy_count, reverse=False)
    popular_beernights = high_rated_beernights[:3] + most_copied_beernights[:3]
    new_beernights = sorted(beernights, key=lambda x: x.created_at, reverse=True)[:15]
    #random_new = random.sample(new_beernights, min(len(new_beernights), 5))
    categories = {}
    cat_names = []
    for b in beernights:
        if b.category:
            if not b.category in categories:
                categories[b.category] = [b]
                cat_names.append(b.category)
            else:
                categories[b.category].append(b)
    
    return render_template(
        'public_beernights.jinja',
        beernights=beernights_sorted,
        featured_beernights=featured_beernights,
        popular_beernights=popular_beernights,
        new_beernights=new_beernights[:5],
        categories=categories,
        cat_names=cat_names,
        section='beernight')

@beernight.route('/beernights/random_beernight')
def random_beernight():
    beernights = Beernight.query\
            .filter(Beernight.is_public == True).all()
    beernight_id = random.choice(beernights).id
    return redirect(url_for('beernight.beernight_detail', id=beernight_id))

@beernight.route('/beernight/<int:id>', methods=['GET', 'POST'])
@login_required
def beernight_detail(id):
    user = current_user
    beernight = Beernight.query.get(id)
    rating = beernight.average_rating
    beers = beernight.beers
    form = CopyBeernightForm(request.form)
    if request.method == 'POST':
        if form.validate():
            try:
                new_beernight = copy_public_beernight(form, id)
                if new_beernight:
                    flash("Tókst að afrita bjórkvöld {} til {}.".format(
                                beernight.name, new_beernight.name),
                                category="success")
                    return redirect(url_for('beernight.beernight_detail', id=new_beernight.id))
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
        return redirect(url_for('beernight.beernight_detail', id=beernight.id))
    return render_template(
        'beernight.jinja',
        beernight=beernight,
        beers=beers,
        rating=rating,
        copy_beernight_form=form,
        section='beernight')

@beernight.route('/beernight/beer/<int:id>/create', methods=['GET', 'POST'])
@login_required
@roles_accepted(['admin'])
def beernight_create_beer(id):
    form = BeernightbeerForm(request.form)
    if request.method == 'POST':
        if form.validate():
            try:
                beer = make_beernightbeer(form, id)
                if beer:
                    flash("Tókst að búa til bjór {}.".format(
                                beer.name),
                                category="success")
                    return redirect(url_for('beernight.beernight_detail', id=id))
                else:
                    flash(
                        "Ekki tókst að búa til bjór.",
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
    return render_template(
        'forms/model.jinja',
        form=form,
        action=url_for('beernight.beernight_create_beer', id=id),
        section='beernight',
        type='create')


@beernight.route('/beernight/<int:id>/rate', methods=['POST'])
@login_required
@roles_accepted(['admin', 'Notandi'])
def beernight_rate(id):
    try:
        beernight = Beernight.query.get(id)
        input_rating = request.form.get('value')
        rating = add_beernight_rating(current_user.id, beernight, input_rating)
        response = {}
        return Response(json.dumps(response), status=200)
    except Exception as error:
        app.logger.error('Error creating a verification : {}\n{}'.format(
            error, traceback.format_exc()))
        return Response(error, status=500)


@beernight.route('/beer/<int:id>/add_beer_to_beernight/<int:beernight_id>/')
@login_required
@roles_accepted(['admin', 'Notandi'])
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

@beernight.route('/beer/<int:id>/delete_beer_from_beernight/<int:beernight_id>')
@login_required
@roles_accepted(['admin', 'Notandi'])
def delete_beer_from_beernight(id, beernight_id):
    try:
        beernight = delete_beer_from_beernight_db(id)
        if(beernight):
            flash('Bjór var fjarlægður úr bjórkvöldi',
                    category="success")
        else:
            flash('Ekki tókst að fjarlægja bjór úr bjórkvöldi',
                    category="warning")
        return redirect(url_for('beernight.beernight_detail', id=beernight_id))
    except Exception as error:
        flash('Ekki tókst að senda athugasemd',
                    category="warning")
        app.logger.error('Error creating a verification : {}\n{}'.format(
            error, traceback.format_exc()))
        return Response(error, status=500)

@beernight.route('/beer/beernightbeer/<int:id>/rate', methods=['POST'])
@login_required
@roles_accepted(['admin', 'Notandi'])
def beernight_beer_rate(id):
    try:
        beer = BeernightBeer.query.get(id)
        input_rating = request.form.get('value')
        input_type = request.form.get('type')
        rating = add_beernight_beer_rating(current_user.id, beer, input_rating, input_type)
        response = {
            'beer_id': beer.id,
            'user_id': current_user.id,
            'beer_percentage': beer.getUserRatingPercentage(current_user.id),
            'user_percentage': beer.beernight.user_ratings_finished_percentage(current_user.id),
            'beernight_percentage': beer.beernight.percentage_finished,
            }
        print(response)
        return Response(json.dumps(response), status=200)
    except Exception as error:
        app.logger.error('Error creating a verification : {}\n{}'.format(
            error, traceback.format_exc()))
        return Response(error, status=500)


@beernight.route('/add_user_to_beernight/<int:beernight_id>/', methods=['POST'])
@login_required
def send_beernight_invitation(beernight_id):
    input_user = request.form.get('text')
    if input_user == current_user.email:
        response = {'error': 'Ekki er hægt að bjóða sjálfum sér'}
        return Response(json.dumps(response), status=500)
    user = User.query.filter(User.email == input_user).first()
    if user:
        invite = send_beernight_invitation_db(user, beernight_id)
        if "invite" in invite:
            flash('Boð sent til {}'.format(input_user), category="success")
            response = {'url': url_for('beernight.beernight_detail', id=beernight_id)}
            return Response(json.dumps(response), status=200)
        if "error" in invite:
            response = {'error': invite['error'], 'url': url_for('beernight.beernight_detail', id=beernight_id)}
            return Response(json.dumps(response), status=500)
    else:
        response = {'error': 'Notandi ekki til', 'url': url_for('beernight.beernight_detail', id=beernight_id)}
        return Response(json.dumps(response), status=500)

    response = {'error': 'Ekki tókst að senda boð'}
    return Response(json.dumps(response), status=500)


@beernight.route('/accept_beernight_invite/<int:id>/')
@login_required
def accept_beernight_invite(id):
    res = accept_beernight_invitation_db(id)
    if res:
        flash('Boð samþykkt', category="success")
    else:
        flash('Ekki tókst að samþykkja boð', category="success")
    return redirect(url_for('user.current_user_detail')) 

@beernight.route('/decline_beernight_invite/<int:id>/')
@login_required
def decline_beernight_invite(id):
    res = delete_beernight_invitation_db(id)
    if res:
        flash('Boði eytt', category="success")
    else:
        flash('Ekki tókst að eyða boði', category="success")
    return redirect(url_for('user.current_user_detail')) 

@beernight.route('/beernight/<int:id>/make_user_admin/<int:member_id>')
@login_required
@roles_accepted(['admin', 'Notandi'])
def beernight_make_member_admin(id, member_id):
    try:
        member = User.query.get(member_id)
        beernight = Beernight.query.get(id)
        if beernight.is_user_admin(current_user.id):
            if not beernight.is_user_admin(member_id):
                beernight = make_member_admin(id, member_id)
                if beernight:
                    flash('{} var gerður að stjórnanda'.format(member.name), category="success")
                else:
                    flash('Ekki tókst að gera að stjórnanda'.format(member.name), category="danger")
            else:
                flash('{} er nú þegar stjórnandi'.format(member.name), category="warning")
        else:
            flash('Notandi hefur ekki leyfi fyrir aðgerð', category="warning")
        return redirect(url_for('beernight.beernight_detail', id=id)) 
    except Exception as error:
        app.logger.error('Error creating a verification : {}\n{}'.format(
            error, traceback.format_exc()))
        return redirect(url_for('beernight.beernight_detail', id=id)) 


@beernight.route('/beernight/<int:id>/remove_member/<int:member_id>')
@login_required
@roles_accepted(['admin', 'Notandi'])
def beernight_remove_member(id, member_id):
    try:
        member = User.query.get(member_id)
        beernight = Beernight.query.get(id)
        if beernight.is_user_admin(current_user.id):
            if not beernight.is_user_admin(member_id):
                beernight = remove_member_from_beernight(id, member_id)
                if(beernight):
                    flash('{} var fjarlægður'.format(member.name), category="success")
                else:
                    flash('Ekki tókst að fjarlægja meðlim'.format(member.name), category="danger")

            else:
                flash('{} ekki hægt að fjarlægja stjórnanda'.format(member.name), category="warning")
        else:
            flash('Notandi hefur ekki leyfi fyrir aðgerð', category="warning")
        return redirect(url_for('beernight.beernight_detail', id=id)) 
    except Exception as error:
        app.logger.error('Error creating a verification : {}\n{}'.format(
            error, traceback.format_exc()))
        return redirect(url_for('beernight.beernight_detail', id=id)) 

@beernight.route('/beernight/<int:id>/results', methods=['GET', 'POST'])
@login_required
@roles_accepted(['admin', 'Notandi'])
def beernight_result(id):
    beernight = Beernight.query.get(id)
    beers = beernight.beers
    beer_info = []
    bar_chart_beer = {'names': [], 'mean_ratings': [], 'sight': [], 'smell': [], 'taste':[], 'feel':[], 'rating':[]}
    for b in beers:
        info = {
            "name": b.get_att('name'),
            "overall_rating": b.get_mean_overall_rating if b.get_mean_overall_rating else "-",
            "smell": b.average_cat_rating('smell') if b.average_cat_rating('smell') else "-",
            "sight": b.average_cat_rating('sight') if b.average_cat_rating('sight') else "-",
            "taste": b.average_cat_rating('taste') if b.average_cat_rating('taste') else "-",
            "feel": b.average_cat_rating('feel') if b.average_cat_rating('feel') else "-",
            "rating": b.average_cat_rating('rating') if b.average_cat_rating('rating') else "-",
            }
        beer_info.append(info)
        bar_chart_beer['names'].append(b.get_att('name'))
        bar_chart_beer['mean_ratings'].append(b.get_mean_overall_rating if b.get_mean_overall_rating else "-")
        bar_chart_beer['smell'].append(b.average_cat_rating('smell') if b.average_cat_rating('smell') else "-")
        bar_chart_beer['sight'].append(b.average_cat_rating('sight') if b.average_cat_rating('sight') else "-")
        bar_chart_beer['taste'].append(b.average_cat_rating('taste') if b.average_cat_rating('taste') else "-")
        bar_chart_beer['feel'].append(b.average_cat_rating('feel') if b.average_cat_rating('feel') else "-")
        bar_chart_beer['rating'].append(b.average_cat_rating('rating') if b.average_cat_rating('rating') else "-")
    users = []
    users_names = []
    for m in beernight.members:
        user = {'name': m.name, 'mean_ratings': [], 'sight': [], 'smell': [], 'taste':[], 'feel':[], 'rating':[]}
        for b in beers:
            user['mean_ratings'].append(b.mean_rating_user(m.id) if b.mean_rating_user(m.id) else '-')
            user['sight'].append(b.cat_rating_user('sight',m.id) if b.cat_rating_user('sight', m.id) else '-')
            user['smell'].append(b.cat_rating_user('smell',m.id) if b.cat_rating_user('smell', m.id) else '-')
            user['taste'].append(b.cat_rating_user('taste',m.id) if b.cat_rating_user('taste', m.id) else '-')
            user['feel'].append(b.cat_rating_user('feel',m.id) if b.cat_rating_user('feel', m.id) else '-')
            user['rating'].append(b.cat_rating_user('rating',m.id) if b.cat_rating_user('rating', m.id) else '-')
        users.append(user)
        if m.name in users_names:
            users_names.append('{}({})'.format(m.name,m.email))
        else:
            users_names.append(m.name)

    beers_members_info = {}
    for b in beers:
        beer = {'name': b.get_att('name'), 'mean_ratings': [], 'sight': [], 'smell': [], 'taste':[], 'feel':[], 'rating':[]}
        for m in beernight.members:
            beer['mean_ratings'].append(b.mean_rating_user(m.id) if b.mean_rating_user(m.id) else '-')
            beer['sight'].append(b.cat_rating_user('sight',m.id) if b.cat_rating_user('sight', m.id) else '-')
            beer['smell'].append(b.cat_rating_user('smell',m.id) if b.cat_rating_user('smell', m.id) else '-')
            beer['taste'].append(b.cat_rating_user('taste',m.id) if b.cat_rating_user('taste', m.id) else '-')
            beer['feel'].append(b.cat_rating_user('feel',m.id) if b.cat_rating_user('feel', m.id) else '-')
            beer['rating'].append(b.cat_rating_user('rating',m.id) if b.cat_rating_user('rating', m.id) else '-')
        beers_members_info[b.get_att('name')]=beer
    return render_template(
        'beernight_results.jinja',
        beernight=beernight,
        beer_info=beer_info,
        bar_chart_beer=bar_chart_beer,
        users=users,
        beers_members_info=beers_members_info,
        users_names=users_names,
        section='beernight'
    )



@beernight.route('/beernight/<int:id>/stream_zip')
@login_required
@roles_accepted(['admin', 'Notandi'])
@member_of_beernight(id)
def stream_beernight_zip_results(id):
    beernight = Beernight.query.get(id)
    today = date.today()
    sample_data=[0, 1, 2]
    excel.init_excel(app)
    extension_type = "csv"
    filename = "{}_results_{}.{}".format(beernight.name.replace(" ", "_"), today.strftime("%b-%d-%Y"),extension_type)
    beers = beernight.beers
    beernames = []
    members = []
    sight = []
    smell = []
    taste = []
    feel = []
    rating = []
    mean_score = []
    for b in beers:
        for m in beernight.members:
            beernames.append(b.get_att('name'))
            members.append(m.name)
            sight.append(b.cat_rating_user('sight',m.id) if b.cat_rating_user('sight', m.id) else '')
            smell.append(b.cat_rating_user('smell',m.id) if b.cat_rating_user('smell', m.id) else '')
            taste.append(b.cat_rating_user('taste',m.id) if b.cat_rating_user('taste', m.id) else '')
            feel.append(b.cat_rating_user('feel',m.id) if b.cat_rating_user('feel', m.id) else '')
            rating.append(b.cat_rating_user('rating',m.id) if b.cat_rating_user('rating', m.id) else '')
            mean_score.append(b.mean_rating_user(m.id) if b.mean_rating_user(m.id) else '')


    d = {
        'Bjór': beernames,
        'Þátttakandi': members,
        'Ásýnd': sight,
        'Lykt': smell,
        'Bragð': taste,
        'Áferð': feel,
        'Geðþáttaákvörðun': rating,
        'Heildareinkunn': mean_score,
        }

    return excel.make_response_from_dict(d, file_type=extension_type, file_name=filename)

@beernight.route('/beernight/<int:id>/set_featured')
@login_required
@roles_accepted(['admin'])
def beernight_set_featured(id):
    try:
        beernight = Beernight.query.get(id)
        if not beernight.is_featured and beernight.is_public:
            beernight.is_featured = True
            db.session.commit()
        flash('Gekk að merkja sem meðmæli', category="success")
        return redirect(url_for('beernight.beernight_detail', id=id))
    except Exception as error:
        app.logger.error('Error creating a verification : {}\n{}'.format(
            error, traceback.format_exc()))
        flash('Ekki gekk að merkja sem meðmæli', category="danger")
        return redirect(url_for('beernight.beernight_detail', id=id)) 
    

@beernight.route('/beernight/<int:id>/remove_featured')
@login_required
@roles_accepted(['admin'])
def beernight_remove_featured(id):
    try:
        beernight = Beernight.query.get(id)
        if beernight.is_featured:
            beernight.is_featured = False
            db.session.commit()
        flash('Gekk að afmerkja sem meðmæli', category="success")
        return redirect(url_for('beernight.beernight_detail', id=id))
    except Exception as error:
        app.logger.error('Error creating a verification : {}\n{}'.format(
            error, traceback.format_exc()))
        flash('Ekki gekk að afmerkja sem meðmæli', category="danger")
        return redirect(url_for('beernight.beernight_detail', id=id)) 