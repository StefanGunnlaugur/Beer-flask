import contextlib
import os
import uuid
import wave
import json
import subprocess
import random
import numpy as np
import math
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

user_beernight_memeber = db.Table(
    'user_beernight_memeber',
    db.Column('user_id', db.Integer(), db.ForeignKey('user.id')),
    db.Column('beernight_id', db.Integer(), db.ForeignKey('beernight.id'))
)

user_beernight_admin = db.Table(
    'user_beernight_admin',
    db.Column('user_id', db.Integer(), db.ForeignKey('user.id')),
    db.Column('beernight_id', db.Integer(), db.ForeignKey('beernight.id'))
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
    avatar = db.Column(db.String(200))
    active = db.Column(db.Boolean, default=False)
    tokens = db.Column(db.Text)
    password = db.Column(db.String(255))
    sex = db.Column(db.String(255))
    age = db.Column(db.Integer)
    active = db.Column(db.Boolean())
    game_score = db.Column(db.Integer)
    created_at = db.Column(
        db.DateTime,
        default=db.func.current_timestamp())
    roles = db.relationship(
        'Role',
        secondary=roles_users,
        backref=db.backref('users', lazy='dynamic'))
    beers = db.relationship("Beer",
                    secondary=user_beer)
    beernights_member = db.relationship("Beernight",
                    secondary=user_beernight_memeber,
                    back_populates="members")
    beernights_admin = db.relationship("Beernight",
                    secondary=user_beernight_admin,
                    back_populates="admins")
                            
    invitations = db.relationship(
        "BeernightInvitation", primaryjoin="User.id==BeernightInvitation.receiver_id", back_populates='receiver',
        cascade='all, delete, delete-orphan')

    sent_invitations = db.relationship(
        "BeernightInvitation", primaryjoin="User.id==BeernightInvitation.sender_id", back_populates='sender',
        cascade='all, delete, delete-orphan')


    @property
    def invite_ids(self):
        ids = []
        for i in self.invitations:
            ids.append(i.id)
        return ids

    @property
    def beer_ids(self):
        ids = []
        for b in self.beers:
            ids.append(b.id)
        return ids

    @property
    def admin_beernight_ids(self):
        ids = []
        for b in self.beernights_admin:
            ids.append(b.id)
        return ids
    
    @property
    def member_beernight_ids(self):
        ids = []
        for b in self.beernights_member:
            ids.append(b.id)
        return ids

    @property
    def get_member_beernights(self):
        beernights = []
        for b in self.beernights_member:
            if not b.is_user_admin(self.id):
                beernights.append(b)
        return beernights

    @property
    def user_data_path(self):
        return os.path.join(app.config['USERS_DATA_DIR'], str(self.id))
    
    @property
    def user_beernights_path(self):
        return os.path.join(self.user_data_path, 'beernights')
    
    @property
    def user_other_path(self):
        return os.path.join(self.user_data_path, 'other')

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
    name = db.Column(db.String(255), info={'label': 'Nafn',})
    price = db.Column(db.Integer, info={'label': 'Verð(kr)',})
    alcohol = db.Column(db.Float, info={'label': 'Áfengi(%)',})
    book_score = db.Column(db.Float)
    economic_score = db.Column(db.Float)
    volume = db.Column(db.Integer, info={'label': 'Magn(ml)',})
    country = db.Column(db.String(255), info={'label': 'Land',})
    manufacturer = db.Column(db.String(255), info={'label': 'Framleiðandi',})
    description = db.Column(db.String(500), info={'label': 'Lýsing',})
    beer_type = db.Column(db.String(255), info={'label': 'Tegund'})
    drink_detail = db.Column(db.String(255), info={'label': 'Tegund nánar'})
    category = db.Column(db.String(255), info={'label': 'Flokkur áfengis'})
    vinbud_link = db.Column(db.String(255), info={'label': 'Hlekkur á drykk'})
    product_id = db.Column(db.String(255))
    image_path = db.Column(db.String)
    ratings = db.relationship(
        "BeerRating", lazy="joined", back_populates='beer',
        cascade='all, delete, delete-orphan')
    comments = db.relationship(
        "BeerComment", lazy="joined", back_populates='beer',
        cascade='all, delete, delete-orphan')

    def __init__(self):
        pass
    
    def is_liked_by_user(self, user_id):
        user = User.query.get(user_id)
        for l in user.beers:
            if l.id == self.id:
                return True
        return False

    def getUserRating(self, user_id):
        for r in self.ratings:
            if r.user_id == user_id:
                return r.rating
        return None

    @property
    def get_type(self):
        if not self.beer_type:
            return ''
        else:
            return self.beer_type

    @property
    def calculateBook(self):
        if self.volume and self.alcohol and self.price:
            x = max(1, abs(self.volume - 330))
            y = math.log10(x)
            booksRating = ((self.volume * self.alcohol)/self.price) - max(0, y) + (abs(self.float_average_rating - 3.0) * math.log(1 + len(self.ratings)))
            return round(booksRating, 2)
        return 0

    def getAllUsers(self):
        ratings = self.ratings
        user_ids = []
        for i in ratings:
            user_ids.append(i.user_id)
        user_ids = list(set(user_ids))
        return user_ids
    
    @hybrid_property
    def bang_for_buck(self):
        if self.price and self.alcohol and self.price:
            bfb = (self.volume * (self.alcohol))/self.price
            return round(bfb,2)
        else:
            return 0
    
    @bang_for_buck.expression
    def bang_for_buck(cls):
        if self.price:
            bfb = (cls.volume * (cls.alcohol))/cls.price
            return func.round(bfb,2)
        else:
            return 0


    @property
    def get_printable_id(self):
        return "Bjór-{}".format(self.id)
        

    @property
    def ajax_rate_action(self):
        return url_for('beer.beer_rate', id=self.id)
    
    @property
    def ajax_comment_action(self):
        return url_for('beer.beer_comment', id=self.id)

    @property
    def ajax_favourite_action(self):
        return url_for('beer.beer_favourite', id=self.id)

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
    def float_average_rating(self):
        if self.average_rating == "-":
            return 0
        else:
            return self.average_rating
    
    @property
    def round_rating(self):
        if(len(self.ratings) > 0):
            total_ratings = 0
            for i in self.ratings:
                total_ratings += i.rating
            total_ratings = total_ratings/len(self.ratings)
            return round(total_ratings)
        else:
            return False

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
    beer = db.relationship("Beer", back_populates="ratings")
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __init__(self, user_id, beer, rating):
        self.user_id = user_id
        self.beer = beer
        self.rating = rating

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
    text = db.Column(db.String(255))
    beer_id = db.Column(db.Integer, db.ForeignKey("beer.id"))
    beer = db.relationship("Beer", back_populates="comments")
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    parent_comment_id = db.Column(db.Integer, db.ForeignKey('beerComment.id'))
    replies = db.relationship("BeerComment",
                cascade='all, delete, delete-orphan')
    likes = db.relationship(
        "CommentLike", lazy="joined", back_populates='comment',
        cascade='all, delete, delete-orphan')
    reports = db.relationship(
        "CommentReport", lazy="joined", back_populates='comment',
        cascade='all, delete, delete-orphan')
    
    def __init__(self, user_id, beer, text, parent_comment_id=None):
        self.user_id = user_id
        self.beer = beer
        self.text = text
        if parent_comment_id is not None:
            self.parent_comment_id = parent_comment_id

    @property
    def user(self):
        return User.query.get(self.user_id)

    @property
    def get_beer(self):
        return Beer.query.get(self.beer_id)
    
    @property
    def num_likes(self):
        return len(self.likes)

    @property
    def get_parent_comment(self):
        return BeerComment.query.get(self.parent_comment_id)

    def is_liked_by_user(self, user_id):
        like = CommentLike.query\
            .filter(CommentLike.comment_id == self.id) \
            .filter(CommentLike.user_id == user_id).all()
        if like:
            return True
        return False
    


class CommentLike(BaseModel, db.Model):
    __tablename__ = 'commentLike'
    __table_args__ = (
        db.UniqueConstraint('comment_id', 'user_id'),
      )
    id = db.Column(
        db.Integer, primary_key=True, nullable=False, autoincrement=True)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    comment_id = db.Column(db.Integer, db.ForeignKey("beerComment.id"))
    comment = db.relationship("BeerComment", back_populates="likes")
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __init__(self, user_id, comment_id):
        self.user_id = user_id
        self.comment_id = comment_id

    @property
    def user(self):
        return User.query.get(self.user_id)


class CommentReport(BaseModel, db.Model):
    __tablename__ = 'commentReport'
    __table_args__ = (
        db.UniqueConstraint('comment_id', 'user_id'),
      )
    id = db.Column(
        db.Integer, primary_key=True, nullable=False, autoincrement=True)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    comment_id = db.Column(db.Integer, db.ForeignKey("beerComment.id"))
    comment = db.relationship("BeerComment", back_populates="reports")
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __init__(self, user_id, comment_id):
        self.user_id = user_id
        self.comment_id = comment_id

    @property
    def user(self):
        return User.query.get(self.user_id)



class Beernight(BaseModel, db.Model):
    __tablename__ = 'beernight'
    id = db.Column(
        db.Integer, primary_key=True, nullable=False, autoincrement=True)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    uuid = db.Column(db.String, default=str(uuid.uuid4()))
    ratings = db.relationship(
        "BeernightRating", lazy="joined", back_populates='beernight',
        cascade='all, delete, delete-orphan')
    name = db.Column(
        db.String(255),
        info={
            'validators': [validators.InputRequired()],
            'label': 'Nafn'})
    copy_count = db.Column(db.Integer, default=0)
    is_featured = db.Column(db.Boolean, default=False)
    is_public = db.Column(db.Boolean, default=False, info={
        'label': 'Sýnilegur öllum',
    })
    image_path = db.Column(db.String)
    category = db.Column(
        db.String(255),
        info={'label': 'Flokkur'})
    creator_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    admins = db.relationship(
        "User",
        secondary=user_beernight_admin,
        back_populates="beernights_admin")
    members = db.relationship(
        "User",
        secondary=user_beernight_memeber,
        back_populates="beernights_member")
    beers = db.relationship(
        "BeernightBeer", lazy='joined', backref="beernight")

    invitations = db.relationship(
        "BeernightInvitation", lazy="joined", back_populates='beernight',
        cascade='all, delete, delete-orphan')


    @property
    def data_path(self):
        return os.path.join(self.creator.user_beernights_path, str(self.id))

    @property
    def total_volume(self):
        total_volume = 0
        for b in self.beers:
            total_volume += b.get_att('volume')
        return total_volume

    @property
    def total_alcohol_volume(self):
        total_alcohol = 0
        for b in self.beers:
            total_alcohol += (b.get_att('volume') * (b.get_att('alcohol')/100))
        return round(total_alcohol)

    @property
    def num_ratings_finished(self):
        finished = 0
        for b in self.beers:
            finished += b.getFinishedRatingNumber
        return finished

    @property
    def percentage_finished(self):
        all_ratings = len(self.members)*len(self.beers)*5
        finished = self.num_ratings_finished
        if all_ratings != 0:
            return round((finished/all_ratings)*100)
        else:
            return 0


    def user_ratings_finished_num(self, user_id):
        finished = 0
        for b in self.beers:
            finished += b.getUserRatingNumber(user_id)
        return finished

    def user_ratings_finished_percentage(self,user_id):
        all_ratings = len(self.beers)*5
        finished = self.user_ratings_finished_num(user_id)
        if all_ratings != 0:
            return round((finished/all_ratings)*100)
        else:
            return 0
        
    @property
    def round_rating(self):
        if(len(self.ratings) > 0):
            total_ratings = 0
            for i in self.ratings:
                total_ratings += i.rating
            total_ratings = total_ratings/len(self.ratings)
            return round(total_ratings)
        else:
            return False

    @property
    def beerRatings(self):
        ratings = []
        for m in self.beers:
            for r in m.ratings:
                ratings.append(r)
        return ratings
    
    def is_user_creator(self, user_id):
        if self.creator_id == user_id:
            return True
        return False

    def is_user_admin(self, user_id):
        for i in self.admins:
            if i.id == user_id:
                return True
        return False

    def getUserRating(self, user_id):
        for r in self.ratings:
            if r.user_id == user_id:
                return r.rating
        return None

    def is_user_in_beernight(self, user_id):
        return self.is_user_admin(user_id) or self.is_user_member(user_id)

    def is_user_member(self, user_id):
        for i in self.members:
            if i.id == user_id:
                return True
        return False

    def getAllUserRatings(self, user_id):
        ratings = []
        for m in self.beers:
            for r in m.ratings:
                if user_id == r.user_id:
                    ratings.append(r)
        return ratings

    def getAllUsers(self):
        ratings = self.beerRatings
        user_ids = []
        for i in ratings:
            user_ids.append(i.user_id)
        user_ids = list(set(user_ids))
        return user_ids

    def get_mean_user_rating(self, user_id):
        rating = None
        counter = 0
        for i in self.beerRatings:
            if i.user_id == user_id:
                r = i.get_mean_overall_rating
                if r:
                    if not rating:
                        rating = r
                    else:
                        rating += r
                    counter += 1
        if rating and counter != 0:
            return round(rating/counter, 2)
        return None

    def get_mean_cat_user_rating(self, user_id, cat):
        rating = None
        counter = 0
        for i in self.beerRatings:
            if i.user_id == user_id:
                r = getattr(i, cat)
                if r:
                    if not rating:
                        rating = r
                    else:
                        rating += r
                    counter += 1
        if rating and counter != 0:
            return round(rating/counter, 2)
        return None

    @property
    def creator(self):
        creator = User.query.get(self.creator_id)
        return creator

    @property
    def ajax_rate_action(self):
        return url_for('beernight.beernight_rate', id=self.id)

    @property
    def num_beers(self):
        return len(self.beers)

    @property
    def printable_id(self):
        return "Bjórkvöld-{:04d}".format(self.name)
    
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
    def float_average_rating(self):
        if self.average_rating == "-":
            return 0
        else:
            return self.average_rating

    @property
    def get_copy_count(self):
        if self.copy_count:
            return self.copy_count
        else:
            return 0

    @property
    def std_of_ratings(self):
        ratings = [r.rating for r in self.ratings]
        if len(ratings) == 0:
            return "-"
        ratings = np.array(ratings)
        return round(np.std(ratings), 2)

    @property
    def get_beer_mean_score(self):
        rating = None
        counter = 0
        for c in self.beers:
            r = c.get_mean_overall_rating
            if r:
                if not rating:
                    rating = r
                else:
                    rating += r
                counter += 1
        if rating and counter != 0:
            return round(rating/counter, 2)
        return None
            
    def number_of_ratings_per_user(self, user_id):
        counter = 0
        for i in self.beerRatings:
            if i.user_id == user_id:
                counter += 1
        return counter

    @property
    def number_of_ratings(self):
        return len(self.ratings)

    @property
    def number_of_beer_ratings(self):
        return len(self.beerRatings)

user_beernight = db.Table(
    'user_beernight',
    db.Column('user_id', db.Integer(), db.ForeignKey('user.id')),
    db.Column('beernight_id', db.Integer(), db.ForeignKey('beernight.id'))
)

class BeernightInvitation(BaseModel, db.Model):
    __tablename__ = 'beernightinvitation'
    __table_args__ = (
        db.UniqueConstraint('beernight_id', 'receiver_id'),
      )
    id = db.Column(
        db.Integer, primary_key=True, nullable=False, autoincrement=True)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

    receiver_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    receiver = db.relationship("User", foreign_keys=[receiver_id], back_populates="invitations")

    sender_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    sender = db.relationship("User", foreign_keys=[sender_id], back_populates="sent_invitations")

    beernight_id = db.Column(db.Integer, db.ForeignKey("beernight.id"))
    beernight = db.relationship("Beernight", back_populates="invitations")

    def __init__(self, receiver_id, sender_id, beernight_id):
        self.receiver_id = receiver_id
        self.sender_id = sender_id
        self.beernight_id = beernight_id

class BeernightRating(BaseModel, db.Model):
    __tablename__ = 'beernightRating'
    __table_args__ = (
        db.UniqueConstraint('beernight_id', 'user_id'),
      )
    id = db.Column(
        db.Integer, primary_key=True, nullable=False, autoincrement=True)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    rating = db.Column(db.Integer, default=0, info={
        'label': 'Einkunn',
        'min': 0,
        'max': 5,
    })
    beernight_id = db.Column(db.Integer, db.ForeignKey("beernight.id"))
    beernight = db.relationship("Beernight", back_populates="ratings")
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __init__(self, user_id, beernight_id, rating):
        self.user_id = user_id
        self.beernight_id = beernight_id
        self.rating = rating

    @property
    def get_user(self):
        return User.query.get(self.user_id)

    @property
    def get_beer(self):
        return Beer.query.get(self.beer_id)

class BeernightBeer(BaseModel, db.Model):
    __tablename__ = 'beernightBeer'
    id = db.Column(
        db.Integer, primary_key=True, nullable=False, autoincrement=True)
    beernight_id = db.Column(db.Integer, db.ForeignKey('beernight.id'))
    orginal_beer_id = db.Column(db.Integer, db.ForeignKey("beer.id"))
    orginal_beer = db.relationship("Beer")
    is_custom_made = db.Column(db.Boolean, default=False)
    name = db.Column(db.String(255), info={'label': 'Nafn',})
    price = db.Column(db.Integer, info={'label': 'Verð(kr)',})
    alcohol = db.Column(db.Float, info={'label': 'Áfengi(%)',})
    book_score = db.Column(db.Float)
    economic_score = db.Column(db.Float)
    volume = db.Column(db.Integer, info={'label': 'Magn(ml)',})
    country = db.Column(db.String(255), info={'label': 'Land',})
    manufacturer = db.Column(db.String(255), info={'label': 'Framleiðandi',})
    description = db.Column(db.String(500), info={'label': 'Lýsing',})
    beer_type = db.Column(db.String(255), info={'label': 'Tegund',})
    product_number = db.Column(db.Integer)
    image_path = db.Column(db.String)
    ratings = db.relationship(
        "BeernightbeerRating", lazy="joined", back_populates='beer',
        cascade='all, delete, delete-orphan')
    comments = db.relationship(
        "BeernightbeerComment", lazy="joined", back_populates='beer',
        cascade='all, delete, delete-orphan')

    def __init__(self, beer=None):
        self.orginal_beer = beer
    

    @property
    def data_path(self):
        return self.beernight.data_path

    @property
    def getFinishedRatingPercentage(self):
        all_ratings = self.num_all_cat_ratings
        if all_ratings != 0:
            return self.getFinishedRatingNumber/all_ratings
        else:
            return 0

    @property
    def getFinishedRatingNumber(self):
        finished_ratings = 0
        for r in self.ratings:
            finished_ratings += r.finished_categories
        return finished_ratings
    
    @property
    def num_all_cat_ratings(self):
        return len(self.ratings)*5

    def getUserRatingPercentage(self, user_id):
        rating = self.get_user_rating(user_id)
        if rating:
            print(rating.finishedPercentage)
            return rating.finishedPercentage
        return 0

    def getUserRatingNumber(self, user_id):
        rating = self.get_user_rating(user_id)
        if rating:
            return rating.finished_categories
        return 0

    def get_att(self, att):
        if self.orginal_beer:
            a = getattr(self.orginal_beer, att)
            return a
        else:
            return getattr(self, att)
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
    def calculateBook(self):
        x = max(1, abs(self.volume - 330))
        y = math.log10(x)
        booksRating = ((self.volume * self.alcohol)/self.price) - max(0, y) + (abs(self.float_average_rating - 3.0) * math.log(1 + len(self.ratings)))
        return booksRating

    def getAllUsers(self):
        ratings = self.ratings
        user_ids = []
        for i in ratings:
            user_ids.append(i.user_id)
        user_ids = list(set(user_ids))
        return user_ids
    
    @hybrid_property
    def bang_for_buck(self):
        if self.price:
            bfb = (self.volume * (self.alcohol))/self.price
            return round(bfb,2)
        else:
            return 0
    
    @bang_for_buck.expression
    def bang_for_buck(cls):
        if self.price:
            bfb = (cls.volume * (cls.alcohol))/cls.price
            return func.round(bfb,2)
        else:
            return 0


    @property
    def ajax_rate_action(self):
        return url_for('beernight.beernight_beer_rate', id=self.id)

    def get_category_len(self, cat):
        counter = 0
        for i in self.ratings:
            if getattr(i, cat):
                counter += 1
        return counter
    
    def get_user_rating(self, user_id):
        for i in self.ratings:
            if i.user_id == user_id:
                return i
        return None

    @property
    def get_mean_overall_rating(self):
        cats = ['smell', 'sight', 'taste', 'feel', 'rating']
        rating = None
        counter = 0
        for c in cats:
            r = self.average_cat_rating(c)
            if r:
                if not rating:
                    rating = r
                else:
                    rating += r
                counter += 1
        if rating and counter != 0:
            return round(rating/counter, 2)
        return None


    def average_cat_rating(self, cat):
        len_rat = self.get_category_len(cat)
        if(len_rat > 0):
            total_ratings = 0
            for i in self.ratings:
                cat_rat = getattr(i, cat)
                if cat_rat:
                    total_ratings += cat_rat
            total_ratings = total_ratings/len_rat
            return round(total_ratings, 2)
        else:
            return None

    def cat_rating_user(self, cat, user_id):
        len_rat = self.get_category_len(cat)
        if(len_rat > 0):
            for i in self.ratings:
                if i.user_id == user_id:
                    cat_rat = getattr(i, cat)
                    if cat_rat:
                        return cat_rat
        return None

    def mean_rating_user(self, user_id):
        for i in self.ratings:
            if i.user_id == user_id:
                return i.get_mean_overall_rating
        return None

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


class BeernightbeerRating(BaseModel, db.Model):
    __tablename__ = 'beernightbeerRating'
    __table_args__ = (
        db.UniqueConstraint('beer_id', 'user_id'),
      )
    id = db.Column(
        db.Integer, primary_key=True, nullable=False, autoincrement=True)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    rating = db.Column(db.Integer, default=0, info={
        'label': 'Geðþáttaeinkunn',
        'min': 0,
        'max': 5,
    })
    taste = db.Column(db.Integer, default=0, info={
        'label': 'Bragð',
        'min': 0,
        'max': 5,
    })
    smell = db.Column(db.Integer, default=0, info={
        'label': 'Lykt',
        'min': 0,
        'max': 5,
    })
    feel = db.Column(db.Integer, default=0, info={
        'label': 'Áferð',
        'min': 0,
        'max': 5,
    })
    sight = db.Column(db.Integer, default=0, info={
        'label': 'Ásýnd',
        'min': 0,
        'max': 5,
    })
    
    beer_id = db.Column(db.Integer, db.ForeignKey("beernightBeer.id"))
    beer = db.relationship("BeernightBeer", back_populates="ratings")
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    
    def __init__(self, user_id, beer):
        self.user_id = user_id
        self.beer = beer
    
    def get_category_len(self, cat):
        return len(getattr(self, cat))

    @property
    def finishedPercentage(self):
        return round((self.finished_categories/5)*100)
    
    @property
    def finished_categories(self):
        counter = 0
        if self.rating:
            counter += 1
        if self.taste:
            counter += 1
        if self.smell:
            counter += 1
        if self.feel:
            counter += 1
        if self.sight:
            counter += 1
        return counter

    @property
    def get_mean_overall_rating(self):
        cats = ['smell', 'sight', 'taste', 'feel', 'rating']
        rating = None
        counter = 0
        for c in cats:
            r = getattr(self, c)
            if r:
                if not rating:
                    rating = r
                else:
                    rating += r
                counter += 1
        if rating and counter != 0:
            return round(rating/counter, 2)
        return None

    @property
    def get_user(self):
        return User.query.get(self.user_id)

    @property
    def get_beer(self):
        return Beer.query.get(self.beer_id)



class BeernightbeerComment(BaseModel, db.Model):
    __tablename__ = 'beernightbeerComment'
    id = db.Column(
    db.Integer, primary_key=True, nullable=False, autoincrement=True)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())    
    text = db.Column(db.String(255))
    beer_id = db.Column(db.Integer, db.ForeignKey("beernightBeer.id"))
    beer = db.relationship("BeernightBeer", back_populates="comments")
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    parent_comment_id = db.Column(db.Integer, db.ForeignKey('beernightbeerComment.id'))
    replys = db.relationship("BeernightbeerComment",
                backref=db.backref('parent_comment', single_parent=True, remote_side=[id],
                cascade='all, delete, delete-orphan')
            )
    def __init__(self, user_id, beer, text):
        self.user_id = user_id
        self.beer = beer
        self.text = text

    @property
    def get_user(self):
        return User.query.get(self.user_id)

    @property
    def get_beer(self):
        return Beer.query.get(self.beer_id)
    
    @property
    def get_parent_comment(self):
        return BeerComment.query.get(self.parent_comment_id)