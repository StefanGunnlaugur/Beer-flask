import datetime
import json
import math
import os
import secrets
from os import path
import traceback
from PIL import Image

from flask import current_app as app
import csv
from pydub import AudioSegment
from pydub.utils import mediainfo
import pathlib
from werkzeug import secure_filename
from collections import defaultdict
from flask import flash
from sqlalchemy import func
from flask_security import current_user
from skal.models import (User, db, Beer, BeerRating, BeerComment, Beernight,
                        BeernightRating, CommentLike, CommentReport,
                        BeernightBeer, BeernightBeer, BeernightbeerComment, BeernightbeerRating,
                        BeernightRating, BeernightInvitation)


def resolve_order(object, sort_by, order='desc'):
    ordering = getattr(object, sort_by)
    if callable(ordering):
        ordering = ordering()
    if str(order) == 'asc':
        return ordering.asc()
    else:
        return ordering.desc()


def save_picture(form_picture):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(app.config['BEERS_IMAGE_DIR'], picture_fn)
    output_size = (612, 612)
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)
    return picture_fn

def make_beer(form, image):
    try:
        beer = Beer()
        form.populate_obj(beer)
        beer.book_score = beer.calculateBook
        db.session.add(beer)
        db.session.commit()
        if beer:
            picture_file = save_picture(image)
            if picture_file:
                if beer.image_path:
                    if path.exists(os.path.join(app.config['BEERS_IMAGE_DIR'], beer.image_path)):
                        os.remove(os.path.join(app.config['BEERS_IMAGE_DIR'], beer.image_path))
                beer.image_path = picture_file
                db.session.commit()
        return beer
    except Exception as e:
        print(e)
    return False

def delete_beer_rating_if_exists(beer_id, user_id):
    rating = BeerRating.query\
        .filter(BeerRating.beer_id == beer_id) \
        .filter(BeerRating.user_id == user_id).all()
    exists = False
    for r in rating:
        exists = True
        db.session.delete(r)
    db.session.commit()
    return exists


def add_beer_rating(user_id, beer, rating):
    try:
        delete_beer_rating_if_exists(beer.id, user_id)
        if(rating != 0):     
            beer_rating = BeerRating(user_id, beer, rating)
            db.session.add(beer_rating)
            db.session.commit()
            return beer_rating
        return True
    except Exception as e:
        print(e)
    return False

def check_cat_input(cat):
    return cat in ['rating', 'taste', 'smell', 'feel', 'sight']

def add_beernight_beer_rating(user_id, beer, grade, category):
    if not check_cat_input(category):
        return False

    try:
        rating = BeernightbeerRating.query\
            .filter(BeernightbeerRating.beer_id == beer.id) \
            .filter(BeernightbeerRating.user_id == user_id).first()
        if rating:
            if(grade == 0):
                setattr(rating, category, None)
            else:
                setattr(rating, category, grade)
            
        else:
            rating = BeernightbeerRating(user_id, beer)
            setattr(rating, category, grade)
            db.session.add(rating)
        db.session.commit()
        return rating

    except Exception as e:
        print(e)
    return False

def add_beer_comment(user_id, beer, text, parent_id=None):
    try:
        if(text and beer):     
            beer_comment = BeerComment(user_id, beer, text, parent_id)
            db.session.add(beer_comment)
            db.session.commit()
            print(beer_comment)
            print(beer_comment.parent_comment_id)
            return beer_comment
        return True
    except Exception as e:
        print(e)
    return False

def delete_favourite_if_exists(beer_id, user):
    beers = user.beers
    favs = []
    for b in beers:
        if b.id == beer_id:
            favs.append(b)
    if favs:
        for f in favs:
            user.beers.remove(f)
        db.session.commit()
        return True
    return False


def add_beer_favourite(user, beer, fav):
    user_id = user.id
    try:
        delete = delete_favourite_if_exists(beer.id, user)
        if not delete:
            user.beers.append(beer)
            db.session.commit()
            return True
        return False
    except Exception as e:
        print(e)
    return False

def delete_beernight_rating_if_exists(beernight_id, user_id):
    rating = BeernightRating.query\
        .filter(BeernightRating.beernight_id == beernight_id) \
        .filter(BeernightRating.user_id == user_id).all()
    exists = False
    for r in rating:
        exists = True
        db.session.delete(r)
    db.session.commit()
    return exists

def add_beernight_rating(user_id, beernight, rating):
    try:
        delete_beernight_rating_if_exists(beernight.id, user_id)
        if(rating != 0):     
            beernight_rating = BeernightRating(user_id, beernight.id, rating)
            db.session.add(beernight_rating)
            db.session.commit()
            return beernight_rating
        return True
    except Exception as e:
        print(e)
    return False

def make_beernight(form, beer, user):
    try:
        beernight = Beernight()
        form.populate_obj(beernight)
        beernight.creator_id = user.id
        beernight.admins.append(user)
        beernight.members.append(user)
        if beer:
            beernightBeer = BeernightBeer(beer)
            db.session.add(beernightBeer)
            db.session.flush()
            beernight.beers.append(beernightBeer)
        db.session.add(beernight)
        db.session.commit()
        os.mkdir(os.path.join(user.user_beernights_path, str(beernight.id)))
        return beernight
    except Exception as e:
        print(e)
    return None


def save_beernight_beer_picture(form_picture, beer):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(beer.data_path, picture_fn)
    output_size = (612, 612)
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)
    return picture_fn


def make_beernightbeer(form, beernight_id, image):
    try:
        beernight = Beernight.query.get(beernight_id)
        beer = BeernightBeer()
        form.populate_obj(beer)
        beer.is_custom_made = True
        db.session.add(beer)
        db.session.flush()
        beernight.beers.append(beer)
        db.session.commit()
        if beer:
            picture_file = save_beernight_beer_picture(image, beer)
            if picture_file:
                if beer.image_path:
                    if path.exists(os.path.join(beer.data_path, beer.image_path)):
                        os.remove(os.path.join(beer.data_path, beer.image_path))
                beer.image_path = picture_file
                db.session.commit()
        return beer
    except Exception as e:
        print(e)
    return False

def make_member_admin(beernight_id, member_id):
    try:
        beernight = Beernight.query.get(beernight_id)
        member = User.query.get(member_id)
        beernight.admins.append(member)
        db.session.commit()
        return beernight
    except Exception as e:
        print(e)
    return None

def remove_member_from_beernight(beernight_id, member_id):
    try:
        beernight = Beernight.query.get(beernight_id)
        member = User.query.get(member_id)
        beernight.members.remove(member)
        db.session.commit()
        return beernight
    except Exception as e:
        print(e)
    return None

def send_beernight_invitation_db(user, beernight_id):
    beernight = Beernight.query.get(beernight_id)
    invite = BeernightInvitation.query \
            .filter(BeernightInvitation.beernight_id == beernight_id) \
            .filter(BeernightInvitation.receiver_id == user.id).first()
    if invite or beernight.is_user_in_beernight(user.id):
        return {'error':'Notandi þegar með boð eða þegar í smökkuni'}
    try:
        invite = BeernightInvitation(user.id, current_user.id, beernight_id)
        db.session.add(invite)
        db.session.commit()
        return {'invite':invite}
    except Exception as e:
        print(e)
    return {'error':'Eitthvað fór úrskeiðis'}

def delete_beernight_invitation_db(beernight_invitation_id):
    try:
        invite = BeernightInvitation.query.get(beernight_invitation_id)
        if invite.beernight.is_user_admin(current_user.id) or current_user.id == invite.receiver_id:
            db.session.delete(invite)
            db.session.commit()
            return True
        return False
    except Exception as e:
        print(e)
    return None

def accept_beernight_invitation_db(beernight_invitation_id):
    try:
        invite = BeernightInvitation.query.get(beernight_invitation_id)
        if invite.receiver_id == current_user.id:
            beernight = Beernight.query.get(invite.beernight_id)
            beernight.members.append(current_user)
            delete_beernight_invitation_db(beernight_invitation_id)
            db.session.commit()
            return True
        return False
    except Exception as e:
        print(e)
    return None

def make_member_beernight_admin(beernight_id, member_id):
    try:
        beernight = Beernight.query.get(beernight_id)
        member = User.query.get(member_id)
        if not beernight.is_user_admin(member_id) and beernight.is_user_member(member_id):
            beernight.admins.append(member)
            db.session.commit()
            return True
        return False
    except Exception as e:
        print(e)
    return None


def copy_public_beernight(form, beernight_id):
    try:
        old_beernight = Beernight.query.get(beernight_id)
        if old_beernight.is_public:
            beernight = Beernight()
            form.populate_obj(beernight)
            beernight.admins.append(current_user)
            beernight.creator_id = current_user.id
            beernight.category = old_beernight.category
            for b in old_beernight.beers:
                beernightBeer = BeernightBeer(b.orginal_beer)
                db.session.add(beernightBeer)
                db.session.flush()
                beernight.beers.append(beernightBeer)
            old_beernight.copy_count += 1
            db.session.add(beernight)
            db.session.commit()
            os.mkdir(os.path.join(current_user.user_beernights_path, str(beernight.id)))
            return beernight
        return False
    except Exception as e:
        print(e)
    return None

def delete_beer_from_beernight_db(beer_id):
    try:
        beer = BeernightBeer.query.get(beer_id)
        db.session.delete(beer)
        db.session.commit()
        return True
    except Exception as e:
        print(e)
    return None

def add_beer_to_beernight_db(beer_id, beernight_id):
    try:
        beernight = Beernight.query.get(beernight_id)
        beer = Beer.query.get(beer_id)
        beernightBeer = BeernightBeer(beer)
        db.session.add(beernightBeer)
        db.session.flush()
        beernight.beers.append(beernightBeer)
        db.session.commit()
        return beernight
    except Exception as e:
        print(e)
    return None

def report_comment_db(comment_id, user_id):
    try:
        report = CommentReport.query\
            .filter(CommentReport.comment_id == comment_id) \
            .filter(CommentReport.user_id == user_id).all()
        if not report:
            report = CommentReport(user_id, comment_id)
            db.session.add(report)
            db.session.commit()
            return True
        return report
    except Exception as e:
        print(e)
    return False

def like_dislike_comment_db(comment_id, user_id):
    try:
        like = CommentLike.query\
            .filter(CommentLike.comment_id == comment_id) \
            .filter(CommentLike.user_id == user_id).all()
        if not like:
            like = CommentLike(user_id, comment_id)
            db.session.add(like)
            db.session.commit()
            return 'like'
        else: 
            for i in like:
                db.session.delete(i)
            db.session.commit()
            return 'dislike'
    except Exception as e:
        print(e)
    return False