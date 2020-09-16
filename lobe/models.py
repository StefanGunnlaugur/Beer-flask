import contextlib
import os
import uuid
import wave
import json
import subprocess
import random
import numpy as np
from datetime import datetime, timedelta

from flask import current_app as app
from flask import url_for
from flask_security import RoleMixin, UserMixin
from flask_sqlalchemy import SQLAlchemy

from sqlalchemy import func
from sqlalchemy.ext.hybrid import hybrid_method, hybrid_property
from werkzeug import secure_filename

from wtforms_components import ColorField
from wtforms import validators

db = SQLAlchemy()

ADMIN_ROLE_ID = 1
ADMIN_ROLE_NAME = "admin"
ESTIMATED_AVERAGE_RECORD_LENGTH = 5


class BaseModel(db.Model):
    """Base data model for all objects"""
    __abstract__ = True

    def __init__(self, *args):
        super().__init__(*args)

    def __repr__(self):
        return '%s(%s)' % (self.__class__.__name__, {
            column: value
            for column, value in self.__dict__.items()})


roles_users = db.Table(
    'roles_users',
    db.Column('user_id', db.Integer(), db.ForeignKey('user.id')),
    db.Column('role_id', db.Integer(), db.ForeignKey('role.id')))

user_beer = db.Table(
    'user_beer',
    db.Column('user_id', db.Integer(), db.ForeignKey('user.id')),
    db.Column('beer_id', db.Integer(), db.ForeignKey('beer.id'))
)

class Role(db.Model, RoleMixin):
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(80), unique=True)
    description = db.Column(db.String(255))


class User(db.Model, UserMixin):
    id = db.Column(
        db.Integer,
        primary_key=True,
        autoincrement=True)
    uuid = db.Column(
        db.String,
        default=str(uuid.uuid4()))
    name = db.Column(db.String(255))
    email = db.Column(
        db.String(255),
        unique=True)
    password = db.Column(db.String(255))
    sex = db.Column(db.String(255))
    age = db.Column(db.Integer)
    active = db.Column(db.Boolean())
    created_at = db.Column(
        db.DateTime,
        default=db.func.current_timestamp())
    roles = db.relationship(
        'Role',
        secondary=roles_users,
        backref=db.backref('users', lazy='dynamic'))
    beers = db.relationship("Beer",
                    secondary=user_beer)


    def get_url(self):
        return url_for('user.user_detail', id=self.id)

    def get_printable_name(self):
        if self.name is not None:
            return self.name
        else:
            return "Nafnlaus notandi"

    def is_admin(self):
        return self.has_role(ADMIN_ROLE_NAME)

    def __str__(self):
        if type(self.name) != str:
            return str("User_{}".format(self.id))
        return self.name

    def get_meta(self):
        '''
        Returns a dictionary of values that are included in meta.json
        when downloading collections
        '''
        return {
            'id': self.id,
            'name': self.get_printable_name(),
            'email': self.email,
            'sex': self.sex,
            'age': self.age}


class Beer(BaseModel, db.Model):
    __tablename__ = 'beer'
    id = db.Column(
        db.Integer, primary_key=True, nullable=False, autoincrement=True)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    name = db.Column(db.String(255))
    price = db.Column(db.Integer)
    alcohol = db.Column(db.Float)
    volume = db.Column(db.Integer)
    country = db.Column(db.String(255))
    manufacturer = db.Column(db.String(255))
    description = db.Column(db.String(500))
    beer_type = db.Column(db.String(255))
    
    ratings = db.relationship(
        "BeerRating", lazy="joined", backref='beer',
        cascade='all, delete, delete-orphan')

    def __init__(self):
        pass

    def getUserRating(self, user_id):
        for r in self.ratings:
            if r.user_id == user_id:
                return r.rating
        return None

    def getAllUsers(self):
        ratings = self.ratings
        user_ids = []
        for i in ratings:
            user_ids.append(i.user_id)
        user_ids = list(set(user_ids))
        return user_ids

    @property
    def beernight(self):
        return Beernight.query.get(self.beernight_id)

    @property
    def get_printable_id(self):
        return "Bjór-{}".format(self.id)
        

    @property
    def ajax_edit_action(self):
        return url_for('beer.beer_edit', id=self.id)

    @property
    def average_rating(self):
        if(len(self.ratings) > 0):
            total_ratings = 0
            for i in self.ratings:
                total_ratings += i.rating
            total_ratings = total_ratings/len(self.ratings)
            return round(total_ratings, 2)
        else:
            return "-"

    @property
    def std_of_ratings(self):
        ratings = [r.rating for r in self.ratings]
        if len(ratings) == 0:
            return "-"
        ratings = np.array(ratings)
        return round(np.std(ratings), 2)

    @property
    def number_of_ratings(self):
        return len(self.ratings)


class BeerRating(BaseModel, db.Model):
    __tablename__ = 'beerRating'
    __table_args__ = (
        db.UniqueConstraint('beer_id', 'user_id'),
      )
    id = db.Column(
        db.Integer, primary_key=True, nullable=False, autoincrement=True)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    rating = db.Column(db.Integer, default=0, info={
        'label': 'Einkunn',
        'min': 0,
        'max': 5,
    })
    beer_id = db.Column(db.Integer, db.ForeignKey("beer.id"))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    @property
    def get_user(self):
        return User.query.get(self.user_id)

    @property
    def get_beer(self):
        return Beer.query.get(self.beer_id)


class BeerComment(BaseModel, db.Model):
    __tablename__ = 'beerComment'
    id = db.Column(
        db.Integer, primary_key=True, nullable=False, autoincrement=True)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())    
    comment = db.Column(db.String(255))
    beer_id = db.Column(db.Integer, db.ForeignKey("beer.id"))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    @property
    def get_user(self):
        return User.query.get(self.user_id)

    @property
    def get_beer(self):
        return Beer.query.get(self.beer_id)



class Beernight(BaseModel, db.Model):
    __tablename__ = 'beernight'
    id = db.Column(
        db.Integer, primary_key=True, nullable=False, autoincrement=True)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    uuid = db.Column(db.String, default=str(uuid.uuid4()))
    beers = db.relationship(
        "BeernightBeer", lazy='joined', backref="beernight",
        cascade='all, delete, delete-orphan')

    def getAllRatings(self):
        ratings = []
        for m in self.beers:
            for r in m.ratings:
                ratings.append(r)
        return ratings

    def getAllUserRatings(self, user_id):
        ratings = []
        for m in self.mos_objects:
            for r in m.ratings:
                if user_id == r.user_id:
                    ratings.append(r)
        return ratings

    def getAllUsers(self):
        ratings = self.getAllRatings()
        user_ids = []
        for i in ratings:
            user_ids.append(i.user_id)
        user_ids = list(set(user_ids))
        return user_ids

    @property
    def printable_id(self):
        return "Bjór-{:04d}".format(self.id)

    @property
    def edit_url(self):
        return url_for('beer.beer_edit', id=self.id)


class BeernightBeer(BaseModel, db.Model):
    __tablename__ = 'beernightBeer'
    id = db.Column(
        db.Integer, primary_key=True, nullable=False, autoincrement=True)
    beernight_id = db.Column(db.Integer, db.ForeignKey('beernight.id'))
    orginal_beer_id = db.Column(db.Integer, db.ForeignKey("beer.id"))
    
    ratings = db.relationship(
        "BeernightRating", lazy="joined", backref='beernightBeer',
        cascade='all, delete, delete-orphan')

    def __init__(self):
        pass

    def getUserRating(self, user_id):
        for r in self.ratings:
            if r.user_id == user_id:
                return r.rating
        return None

    def getAllUsers(self):
        ratings = self.ratings
        user_ids = []
        for i in ratings:
            user_ids.append(i.user_id)
        user_ids = list(set(user_ids))
        return user_ids

    @property
    def beernight(self):
        return Beernight.query.get(self.beernight_id)

    @property
    def get_printable_id(self):
        return "Bjór-{}".format(self.id)
        

    @property
    def ajax_edit_action(self):
        return url_for('beer.beer_edit', id=self.id)

    @property
    def average_rating(self):
        if(len(self.ratings) > 0):
            total_ratings = 0
            for i in self.ratings:
                total_ratings += i.rating
            total_ratings = total_ratings/len(self.ratings)
            return round(total_ratings, 2)
        else:
            return "-"

    @property
    def std_of_ratings(self):
        ratings = [r.rating for r in self.ratings]
        if len(ratings) == 0:
            return "-"
        ratings = np.array(ratings)
        return round(np.std(ratings), 2)

    @property
    def number_of_ratings(self):
        return len(self.ratings)


class BeernightRating(BaseModel, db.Model):
    __tablename__ = 'beernightRating'
    __table_args__ = (
        db.UniqueConstraint('beernight_beer_id', 'user_id'),
      )
    id = db.Column(
        db.Integer, primary_key=True, nullable=False, autoincrement=True)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    rating = db.Column(db.Integer, default=0, info={
        'label': 'Einkunn',
        'min': 0,
        'max': 5,
    })
    beernight_beer_id = db.Column(db.Integer, db.ForeignKey("beernightBeer.id"))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    @property
    def get_user(self):
        return User.query.get(self.user_id)

    @property
    def get_beer(self):
        return Beer.query.get(self.beer_id)


