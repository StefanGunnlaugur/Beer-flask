import json
import traceback
import random
import numpy as np
import os
from os import path
from datetime import date
from zipfile import ZipFile
from operator import itemgetter
from PIL import Image
import imghdr
import secrets

import flask_excel as excel
from flask_babel import gettext
from flask import (Blueprint, Response, send_from_directory, request,
                   render_template, flash, redirect, url_for)
from flask import make_response
from flask import current_app as app
from flask_security import login_required, current_user
from sqlalchemy.exc import IntegrityError
import random
from skal.decorators import (roles_accepted, member_of_beernight, 
                    member_of_or_public_beernight, admin_of_beernight, not_member_of_beernight)
from skal.models import (User, db, Beer, BeerRating, BeerComment, CommentLike, CommentReport,
                        Beernight, BeernightBeer, BeernightbeerComment, BeernightbeerRating)
from skal.db import (resolve_order, add_beer_rating, add_beer_comment, 
                    add_beer_favourite, make_beernight, report_comment_db,
                    like_dislike_comment_db, add_beer_to_beernight_db, 
                    delete_beer_from_beernight_db, add_beernight_beer_rating,
                    send_beernight_invitation_db, accept_beernight_invitation_db,
                    delete_beernight_invitation_db, copy_public_beernight,
                    add_beernight_rating, make_member_admin, remove_member_from_beernight,
                    make_beernightbeer)
from skal.forms import ( BeerEditForm, BeernightForm, CopyBeernightForm, EditBeernightForm,
                        BeernightbeerForm, UploadBeernightImageForm, EditBeernightbeerForm)

beernight = Blueprint(
    'beernight', __name__, template_folder='templates')


@beernight.route('/beernights/')
def public_beernights():
    beernights = Beernight.query\
            .filter(Beernight.is_public == True)
    beernights_sorted = sorted(beernights, key=lambda x: x.name, reverse=False)
    featured_beernights = Beernight.query.filter(Beernight.is_featured == True).filter(Beernight.is_public == True)
    
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
    return redirect(url_for('beernight.beernight_detail', beernight_id=beernight_id))

@beernight.route('/beernight/<int:beernight_id>', methods=['GET', 'POST'])
@member_of_or_public_beernight
def beernight_detail(beernight_id):
    id = beernight_id
    user = current_user
    beernight = Beernight.query.get(id)
    rating = beernight.average_rating
    beers = beernight.beers
    form = CopyBeernightForm(request.form)
    beernight_beer_form = BeernightbeerForm()
    upload_image_form = UploadBeernightImageForm()
    if request.method == 'POST':
        if form.validate():
            try:
                new_beernight = copy_public_beernight(form, id)
                if new_beernight:
                    flash(gettext("Tókst að afrita smökkun {} til {}.".format(
                                beernight.name, new_beernight.name)),
                                category="success")
                    return redirect(url_for('beernight.beernight_detail', beernight_id=new_beernight.id))
                else:
                    flash(
                        gettext("Ekki tókst að afrita smökkun."),
                        category="warning")
            except Exception as error:
                print(error)
                flash(
                    gettext("Ekki tókst að afrita smökkun."),
                    category="warning")
        else:
            flash(
                gettext("Ekki tókst að afrita smökkun."),
                category="warning")
        return redirect(url_for('beernight.beernight_detail', beernight_id=beernight.id))

    response = make_response(render_template(
        'beernight.jinja',
        beernight=beernight,
        beers=beers,
        rating=rating,
        copy_beernight_form=form,
        upload_image_form=upload_image_form,
        beernight_beer_form=beernight_beer_form,
        section='beernight'))
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    return response

@beernight.route('/beernight/beer/<int:beernight_id>/create', methods=['POST'])
@login_required
@admin_of_beernight
def beernight_create_beer(beernight_id):
    id = beernight_id
    beernight = Beernight.query.get(beernight_id)
    form = BeernightbeerForm(request.form)
    if beernight.is_user_admin(current_user.id):
        if form.validate():
            try:
                image_file = request.files['picture']
                if image_file.filename == '':
                    image_file = None
                if not image_file or imghdr.what(image_file) in ['jpg', 'png', 'gif', 'jpeg']:
                    beer = make_beernightbeer(form, beernight_id, image_file)
                    if beer:
                        flash(gettext("Tókst að búa til drykk {}.".format(
                                    beer.name)),
                                    category="success")
                        return redirect(url_for('beernight.beernight_detail', beernight_id=beernight_id))
                    else:
                        flash(
                            gettext("Ekki tókst að búa til drykk."),
                            category="warning")
                else:
                    flash(
                        gettext("Mynd ekki á réttu formi"),
                        category="warning")
                
            except Exception as error:
                print(error)
                flash(
                    gettext("Ekki tókst að búa til drykk."),
                    category="warning")
        else:
            flash(
                gettext("Ekki var fyllt rétt inn í reiti!"),
                category="warning")
    else:
        flash(
            gettext("Ekki tókst að búa til drykk."),
            category="warning")
    return redirect(url_for('beernight.beernight_detail', beernight_id=beernight_id))


@beernight.route('/beernight/<int:beernight_id>/beer/sendImage/<int:id>/')
@member_of_or_public_beernight
def send_beernight_beer_image(id, beernight_id):
    beer = BeernightBeer.query.get(id)
    try:
        if beer.image_path:
            if path.exists(os.path.join(beer.data_path, beer.image_path)):
                return send_from_directory(
                    beer.data_path,
                    beer.image_path)
        if not beer.is_custom_made and beer.orginal_beer:
            return redirect(url_for('beer.send_beer_image', id=beer.orginal_beer.id))
        return send_from_directory(
                app.config['STATIC_DATA_DIR'],
                'defaultBeerImage.png')
    except Exception as error:
        app.logger.error(
            "Error sending a beernight image : {}\n{}".format(
                error, traceback.format_exc()))
    return ''


@beernight.route('/beernight/<int:beernight_id>/rate', methods=['POST'])
@login_required
@member_of_or_public_beernight
def beernight_rate(beernight_id):
    id = beernight_id
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
@admin_of_beernight
def add_beer_to_beernight(id, beernight_id):
    try:
        beernight = add_beer_to_beernight_db(id, beernight_id)
        if(beernight):
            flash(gettext('Drykk bætt við smökkun'),
                    category="success")
        else:
            flash(gettext('Ekki tókst að bæta drykk við smökkun'),
                    category="warning")
        return redirect(url_for('beer.beer_detail', id=id))
    except Exception as error:
        flash(gettext('Ekki tókst að senda athugasemd'),
                    category="warning")
        app.logger.error('Error creating a verification : {}\n{}'.format(
            error, traceback.format_exc()))
        return Response(error, status=500)

@beernight.route('/beer/<int:id>/delete_beer_from_beernight/<int:beernight_id>')
@login_required
@admin_of_beernight
def delete_beer_from_beernight(id, beernight_id):
    
    try:
        beernight = delete_beer_from_beernight_db(id)
        if(beernight):
            flash(gettext('Drykkur var fjarlægður úr smökkun'),
                    category="success")
        else:
            flash(gettext('Ekki tókst að fjarlægja drykk úr smökkun'),
                    category="warning")
        return redirect(url_for('beernight.beernight_detail', beernight_id=beernight_id))
    except Exception as error:
        flash(gettext('Ekki tókst að senda athugasemd'),
                    category="warning")
        app.logger.error('Error creating a verification : {}\n{}'.format(
            error, traceback.format_exc()))
        return Response(error, status=500)

@beernight.route('/beernight/<int:beernight_id>/beernightbeer/<int:id>/rate', methods=['POST'])
@login_required
@member_of_beernight
def beernight_beer_rate(id, beernight_id):
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
        return Response(json.dumps(response), status=200)
    except Exception as error:
        app.logger.error('Error creating a verification : {}\n{}'.format(
            error, traceback.format_exc()))
        return Response(error, status=500)


@beernight.route('/add_user_to_beernight/<int:beernight_id>/', methods=['POST'])
@login_required
@admin_of_beernight
def send_beernight_invitation(beernight_id):
    input_user = request.form.get('text')
    if input_user == current_user.email:
        response = {'error': gettext('Ekki er hægt að bjóða sjálfum sér')}
        return Response(json.dumps(response), status=500)
    user = User.query.filter(User.email == input_user).first()
    if user:
        invite = send_beernight_invitation_db(user, beernight_id)
        if "invite" in invite:
            flash(gettext('Boð sent til {}'.format(input_user)), category="success")
            response = {'url': url_for('beernight.beernight_detail', beernight_id=beernight_id)}
            return Response(json.dumps(response), status=200)
        if "error" in invite:
            response = {'error': invite['error'], 'url': url_for('beernight.beernight_detail', beernight_id=beernight_id)}
            return Response(json.dumps(response), status=500)
    else:
        response = {'error': gettext('Notandi ekki til'), 'url': url_for('beernight.beernight_detail', beernight_id=beernight_id)}
        return Response(json.dumps(response), status=500)

    response = {'error': gettext('Ekki tókst að senda boð')}
    return Response(json.dumps(response), status=500)


@beernight.route('/accept_beernight_invite/<int:beernight_id>/')
@login_required
@not_member_of_beernight
def accept_beernight_invite(beernight_id):
    res = accept_beernight_invitation_db(beernight_id)
    if res:
        flash(gettext('Boð samþykkt'), category="success")
    else:
        flash(gettext('Ekki tókst að samþykkja boð'), category="success")
    return redirect(url_for('user.current_user_detail')) 

@beernight.route('/decline_beernight_invite/<int:beernight_id>/')
@login_required
@not_member_of_beernight
def decline_beernight_invite(beernight_id):
    res = delete_beernight_invitation_db(beernight_id)
    if res:
        flash(gettext('Boði eytt'), category="success")
    else:
        flash(gettext('Ekki tókst að eyða boði'), category="success")
    return redirect(url_for('user.current_user_detail')) 

@beernight.route('/beernight/<int:beernight_id>/make_user_admin/<int:member_id>')
@login_required
@admin_of_beernight
def beernight_make_member_admin(beernight_id, member_id):
    id = beernight_id
    try:
        member = User.query.get(member_id)
        beernight = Beernight.query.get(id)
        if beernight.is_user_admin(current_user.id):
            if not beernight.is_user_admin(member_id):
                beernight = make_member_admin(id, member_id)
                if beernight:
                    flash(gettext('{} var gerður að stjórnanda'.format(member.name)), category="success")
                else:
                    flash(gettext('Ekki tókst að gera {} að stjórnanda'.format(member.name)), category="danger")
            else:
                flash(gettext('{} er nú þegar stjórnandi'.format(member.name)), category="warning")
        else:
            flash(gettext('Notandi hefur ekki leyfi fyrir aðgerð'), category="warning")
        return redirect(url_for('beernight.beernight_detail', beernight_id=id)) 
    except Exception as error:
        app.logger.error('Error creating a verification : {}\n{}'.format(
            error, traceback.format_exc()))
        return redirect(url_for('beernight.beernight_detail', beernight_id=id)) 


@beernight.route('/beernight/<int:beernight_id>/remove_member/<int:member_id>')
@login_required
@admin_of_beernight
def beernight_remove_member(beernight_id, member_id):
    id = beernight_id
    try:
        member = User.query.get(member_id)
        beernight = Beernight.query.get(id)
        if beernight.is_user_admin(current_user.id):
            if not beernight.is_user_admin(member_id):
                beernight = remove_member_from_beernight(id, member_id)
                if(beernight):
                    flash(gettext('{} var fjarlægður'.format(member.name)), category="success")
                else:
                    flash(gettext('Ekki tókst að fjarlægja meðlim'.format(member.name)), category="danger")

            else:
                flash(gettext('{} ekki hægt að fjarlægja stjórnanda'.format(member.name)), category="warning")
        else:
            flash(gettext('Notandi hefur ekki leyfi fyrir aðgerð'), category="warning")
        return redirect(url_for('beernight.beernight_detail', beernight_id=id)) 
    except Exception as error:
        app.logger.error('Error creating a verification : {}\n{}'.format(
            error, traceback.format_exc()))
        return redirect(url_for('beernight.beernight_detail', beernight_id=id)) 

@beernight.route('/beernight/<int:beernight_id>/results', methods=['GET', 'POST'])
@login_required
@member_of_beernight
def beernight_result(beernight_id):
    id = beernight_id
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

@beernight.route('/beernight/<int:beernight_id>/stream_zip')
@login_required
@member_of_beernight
def stream_beernight_zip_results(beernight_id):
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
        gettext('Drykkur'): beernames,
        gettext('Þátttakandi'): members,
        gettext('Ásýnd'): sight,
        gettext('Lykt'): smell,
        gettext('Bragð'): taste,
        gettext('Áferð'): feel,
        gettext('Geðþáttaákvörðun'): rating,
        gettext('Heildareinkunn'): mean_score,
        }

    return excel.make_response_from_dict(d, file_type=extension_type, file_name=filename)

@beernight.route('/beernight/<int:beernight_id>/set_featured')
@login_required
@roles_accepted(['admin'])
def beernight_set_featured(beernight_id):
    id = beernight_id
    try:
        beernight = Beernight.query.get(id)
        if not beernight.is_featured and beernight.is_public:
            beernight.is_featured = True
            db.session.commit()
        flash(gettext('Gekk að merkja sem meðmæli'), category="success")
        return redirect(url_for('beernight.beernight_detail', beernight_id=id))
    except Exception as error:
        app.logger.error('Error creating a verification : {}\n{}'.format(
            error, traceback.format_exc()))
        flash(gettext('Ekki gekk að merkja sem meðmæli'), category="danger")
        return redirect(url_for('beernight.beernight_detail', beernight_id=id)) 
    

@beernight.route('/beernight/<int:beernight_id>/remove_featured')
@login_required
@roles_accepted(['admin'])
def beernight_remove_featured(beernight_id):
    id = beernight_id
    try:
        beernight = Beernight.query.get(id)
        if beernight.is_featured:
            beernight.is_featured = False
            db.session.commit()
        flash(gettext('Gekk að afmerkja sem meðmæli'), category="success")
        return redirect(url_for('beernight.beernight_detail', beernight_id=id))
    except Exception as error:
        app.logger.error('Error creating a verification : {}\n{}'.format(
            error, traceback.format_exc()))
        flash(gettext('Ekki gekk að afmerkja sem meðmæli'), category="danger")
        return redirect(url_for('beernight.beernight_detail', beernight_id=id)) 



@beernight.route("/beernight/<int:beernight_id>/beer/<int:beer_id>/uploadImage/", methods=['POST'])
@login_required
@admin_of_beernight
def uploadBeernightBeerImage(beernight_id, beer_id):
    id = beernight_id
    form = request.files.get('picture')
    beernight = Beernight.query.get(id)
    beer = BeernightBeer.query.get(beer_id)
    if beernight.is_user_admin(current_user.id):
        if imghdr.what(form) in ['jpg', 'png', 'gif', 'jpeg']:
            picture_file = save_Beernight_beer_picture(form, beer)
            if picture_file:
                if beer.image_path:
                    if path.exists(os.path.join(beer.data_path, beer.image_path)):
                        os.remove(os.path.join(beer.data_path, beer.image_path))
                beer.image_path = picture_file
                db.session.commit()
                flash(gettext('Tókst að hlaða upp mynd!'), 'success')
                return redirect(url_for('beernight.beernight_detail', beernight_id=id)) 
    flash(gettext('Ekki tókst að hlaða upp mynd'), 'warning')
    return redirect(url_for('beernight.beernight_detail', beernight_id=id)) 

def save_Beernight_beer_picture(form_picture, beer):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(beer.data_path, picture_fn)
    output_size = (612, 612)
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)
    return picture_fn

@beernight.route("/beernight/uploadImage/<int:beernight_id>", methods=['POST'])
@login_required
@admin_of_beernight
def uploadBeernightImage(beernight_id):
    id = beernight_id
    form = request.files.get('picture')
    beernight = Beernight.query.get(id)
    if beernight.is_user_admin(current_user.id):
        if imghdr.what(form) in ['jpg', 'png', 'gif', 'jpeg']:
            picture_file = save_Beernight_picture(form, beernight)
            if picture_file:
                if beernight.image_path:
                    if path.exists(os.path.join(beernight.data_path, beernight.image_path)):
                        os.remove(os.path.join(beernight.data_path, beernight.image_path))
                beernight.image_path = picture_file
                db.session.commit()
        flash(gettext('Tókst að hlaða upp mynd!'), 'success')
        return redirect(url_for('beernight.beernight_detail', beernight_id=id)) 
    flash(gettext('Ekki tókst að hlaða upp mynd'), 'warning')
    return redirect(url_for('beernight.beernight_detail', beernight_id=id)) 

def save_Beernight_picture(form_picture, beernight):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(beernight.data_path, picture_fn)
    output_size = (612, 612)
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)
    return picture_fn

@beernight.route('/beernight/sendImage/<int:beernight_id>/')
@member_of_or_public_beernight
def send_beernight_image(beernight_id):
    beernight = Beernight.query.get(beernight_id)
    try:
        if beernight.image_path:
            if path.exists(os.path.join(beernight.data_path, beernight.image_path)):
                return send_from_directory(
                    beernight.data_path,
                    beernight.image_path)
        return send_from_directory(
            app.config['STATIC_DATA_DIR'],
            'defaultBeernightImage.png')
    except Exception as error:
        app.logger.error(
            "Error sending a beernight image : {}\n{}".format(
                error, traceback.format_exc()))
    return ''


@beernight.route('/beernight/<int:beernight_id>/beer/<int:beer_id>/edit', methods=['GET', 'POST'])
@admin_of_beernight
def beernight_beer_edit(beernight_id, beer_id):
    form = EditBeernightbeerForm(request.form)
    beer = BeernightBeer.query.get(beer_id)
    if request.method == 'POST' and form.validate():
        try:
            form.populate_obj(beer)
            db.session.commit()
            flash(gettext("Breyting tókst"), category='success')
            return redirect(url_for('beernight.beernight_detail', beernight_id=beernight_id)) 
        except Exception as error:
            flash(gettext("Ekki tókst að breyta"), category='warning')
            app.logger.error('Error updating a user : {}\n{}'.format(
                error, traceback.format_exc()))
    form.name.data = beer.get_att('name')
    form.price.data = beer.get_att('price')
    form.alcohol.data = beer.get_att('alcohol')
    form.volume.data = beer.get_att('volume')
    form.beer_type.data = beer.get_att('beer_type')
    form.category.data = beer.get_att('category')
    #form.country.data = beer.get_att('country')
    #form.manufacturer.data = beer.get_att('manufacturer')
    #form.description.data = beer.get_att('description')
    return render_template(
        'forms/model.jinja',
        form=form,
        action=url_for('beernight.beernight_beer_edit', beernight_id=beernight_id, beer_id=beer_id),
        section='beernight',
        type='edit') 

@beernight.route('/beernight/<int:beernight_id>/edit', methods=['GET', 'POST'])
@admin_of_beernight
def beernight_edit(beernight_id):
    form = EditBeernightForm(request.form)
    beernight = Beernight.query.get(beernight_id)
    if request.method == 'POST' and form.validate():
        try:
            form.populate_obj(beernight)
            db.session.commit()
            flash(gettext("Smökkun var breytt"), category='success')
            return redirect(url_for('beernight.beernight_detail', beernight_id=beernight_id)) 
        except Exception as error:
            flash(gettext("Ekki tókst að breyta smökkun"), category='warning')
            app.logger.error('Error updating a user : {}\n{}'.format(
                error, traceback.format_exc()))
    form.name.data = beernight.name
    form.is_public.data = beernight.is_public
    form.category.data = beernight.category
    return render_template(
        'forms/model.jinja',
        form=form,
        action=url_for('beernight.beernight_edit', beernight_id=beernight_id),
        section='beernight',
        type='edit') 