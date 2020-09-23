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
                        BeernightBeer, BeernightRating)


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

def add_beer_comment(user_id, beer, text, parent_id=None):
    try:
        if(text and beer):     
            beer_comment = BeerComment(user_id, beer, text, parent_id)
            db.session.add(beer_comment)
            db.session.commit()
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

