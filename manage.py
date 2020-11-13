import getpass
import os
import re
import sys
import json
import uuid
import traceback
import datetime
from shutil import copyfile
from tqdm import tqdm
from os import path
from flask_migrate import Migrate, MigrateCommand
from flask_script import Command, Manager
from flask_security.utils import hash_password
from flask_security import (Security, SQLAlchemyUserDatastore)
from sqlalchemy import and_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.exc import MultipleResultsFound, NoResultFound
from termcolor import colored

from skal import app
from skal.models import (User, Role, db, Beer, Beernight, BeernightBeer)


migrate = Migrate(app, db)
manager = Manager(app)


class AddDefaultRoles(Command):
    def run(self):
        roles = [
            {
                "name": "admin",
                "description":
                    'Umsjónarhlutverk með aðgang að notendastillingum',
            },
            {
                "name": "Notandi",
                "description": 'Venjulegur notandi með grunn aðgang',
            },

        ]
        existing_roles = [role.name for role in Role.query.all()]
        for i, r in enumerate(roles):
            if r["name"] not in existing_roles:
                role = Role()
                role.name = r["name"]
                role.description = r["description"]
                db.session.add(role)
                print("Creating role:", r["name"])

        db.session.commit()

def create_directories(user_id):
    if not path.exists(os.path.join(app.config['USERS_DATA_DIR'], str(user_id))):
        user_path = os.path.join(app.config['USERS_DATA_DIR'], str(user_id))
        os.mkdir(user_path)
        os.mkdir(os.path.join(user_path, "beernights"))
        os.mkdir(os.path.join(user_path, "other"))

class AddUserColumns(Command):
    def run(self):
        users = User.query.all()
        for u in users:
            create_directories(u.id)
        

class AddUserRole(Command):
    def run(self):
        users = User.query.all()
        role = Role.query.filter(Role.name == 'admin').first()
        user = User.query.filter(User.email == 'stefangunnlaugur@gmail.com').first()
        user.roles.append(role)
        db.session.commit()

class AddBeerColumns(Command):
    def run(self):
        beers = Beer.query.all()
        for b in beers:
            if b.product_id:
                b.image_path = b.product_id + '.jpg'
            else:
                b.product_id = None
        db.session.commit()

def create_beernight_directories(beernight):
    os.mkdir(os.path.join(beernight.creator.user_beernights_path, str(beernight.id)))


class AddBeernightColumns(Command):
    def run(self):
        beernights = Beernight.query.all()
        for b in beernights:
            create_beernight_directories(b)
        
class AddBeernightBeerColumns(Command):
    def run(self):
        beers = BeernightBeer.query.all()
        for b in beers:
            if not b.name:
                b.name="TempName"
                db.session.commit()
class DeleteUser(Command):
    def run(self):
        users = User.query.all()
        for u in users:
            if u.email != 'stefangunnlaugur@gmail.com':
                print(u)
                app.user_datastore.delete_user(user=u)
        db.session.commit()

class AddUser(Command):
    def run(self):
        email = input("Email: ")
        name = input("Name: ")
        password = get_pw()

        roles = Role.query.all()
        selected_roles = []
        if len(roles) > 0:
            role_select = None
            while role_select not in [r.id for r in roles]:
                print(role_select, [r.id for r in roles])
                print("Select a role")
                role_select = int(input("".join(["[{}] - {} : {}\n".format(
                    role.id, role.name, role.description) for role in roles])))
            selected_roles.append(Role.query.get(role_select).name)
        with app.app_context():
            try:
                app.user_datastore.create_user(
                    email=email, password=hash_password(password),
                    name=name, roles=selected_roles)
                db.session.commit()
                print("User with email {} has been created".format(email))
            except IntegrityError as e:
                print(e)

class AddBeersFromJson(Command):
    def run(self):
        with open('scraper/data-all-13-11-2020.json') as json_file:
            data = json.load(json_file)
            for p in data:
                beer = Beer.query.filter_by(name=p['name']).first()
                if beer is None:
                    beer = Beer()
                    beer.name = p['name']
                if p['price']:
                    beer.price = int(p['price'].replace('.', '').replace(' kr', ''))
                if p['alcohol']:
                    beer.alcohol = float(p['alcohol'].replace('%', ''))
                if p['taste']:
                    beer.beer_type = p['taste']
                if p['type']:
                    beer.drink_detail = p['type']
                if p['volume']:
                    beer.volume = int(p['volume'].replace(' ml', ''))
                if p['product_number']:
                    beer.product_id = str(p['product_number'])
                if p['category']:
                    beer.category = p['category']
                
                beer.image_path = str(p['product_number']) + '.jpg'
                db.session.add(beer)
                beer.economic_score = beer.bang_for_buck
        db.session.commit()
                

class changePass(Command):
    def run(self):
        email = input("Email: ")
        user = User.query.filter_by(email=email).all()
        assert len(user) == 1, "User with email {} was not found".format(email)
        user = user[0]
        password = get_pw()
        user.password = hash_password(password)
        db.session.commit()
        print("Password has been updated")


def get_pw(confirm=True):
    password = getpass.getpass("Password: ")
    if confirm:
        password_confirm = getpass.getpass("Repeat password: ")
        while password != password_confirm:
            print("Passwords must match")
            password = getpass.getpass("Password: ")
            password_confirm = getpass.getpass("Repeat password: ")
    return password


class AddColumnDefaults(Command):
    def run(self):
        users = User.query.filter(User.uuid == None).all()
        for u in users:
            u.uuid = str(uuid.uuid4())
        db.session.commit()



manager.add_command('db', MigrateCommand)
manager.add_command('add_user', AddUser)
manager.add_command('add_role_to_user', AddUserRole)
manager.add_command('delete_users', DeleteUser)
manager.add_command('change_pass', changePass)
manager.add_command('add_default_roles', AddDefaultRoles)
manager.add_command('add_column_defaults', AddColumnDefaults)
manager.add_command('add_beers_from_json', AddBeersFromJson)
manager.add_command('add_beer_columns', AddBeerColumns)
manager.add_command('add_user_columns', AddUserColumns)
manager.add_command('add_beernight_columns', AddBeernightColumns)
manager.add_command('add_beernight_beer_columns', AddBeernightBeerColumns
)


if __name__ == '__main__':
    manager.run()

