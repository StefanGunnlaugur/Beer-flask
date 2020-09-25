import datetime
import json
import math
import os
import traceback
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
from lobe.models import (User, db, Beer, BeerRating, BeerComment, Beernight,
                        BeernightRating, CommentLike, CommentReport,
                        BeernightBeer, BeernightBeer, BeernightbeerComment, BeernightbeerRating,
                        BeernightRating)


def resolve_order(object, sort_by, order='desc'):
    ordering = getattr(object, sort_by)
    if callable(ordering):
        ordering = ordering()
    if str(order) == 'asc':
        return ordering.asc()
    else:
        return ordering.desc()


def delete_rating_if_exists(beer_id, user_id):
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
        delete_rating_if_exists(beer.id, user_id)
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
    return favs


def add_beer_favourite(user, beer, fav):
    user_id = user.id
    try:
        delete_favourite_if_exists(beer.id, user)
        if fav != 'False':
            user.beers.append(beer)
            db.session.commit()
        return True
    except Exception as e:
        print(e)
    return False


def make_beernight(form, beer, user):
    try:
        beernight = Beernight()
        form.populate_obj(beernight)
        beernight.admins.append(user)
        beernightBeer = BeernightBeer(beer)
        db.session.add(beernightBeer)
        db.session.flush()
        beernight.beers.append(beernightBeer)
        db.session.add(beernight)
        db.session.commit()
        return beernight
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