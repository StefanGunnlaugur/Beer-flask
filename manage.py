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

from flask_migrate import Migrate, MigrateCommand
from flask_script import Command, Manager
from flask_security.utils import hash_password
from sqlalchemy import and_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.exc import MultipleResultsFound, NoResultFound
from termcolor import colored

from lobe import app
from lobe.models import (User, Role, db, Beer)


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
        with open('scraper/data-16-09-2020.json') as json_file:
            data = json.load(json_file)
            for p in data:
                beer = Beer.query.filter_by(name=p['name']).first()
                if beer is None:
                    beer = Beer()
                    beer.name = p['name']
                beer.price = int(p['price'].replace('.', '').replace(' kr', ''))
                beer.alcohol = float(p['alcohol'].replace('%', ''))
                beer.beer_type = p['taste']
                beer.volume = int(p['volume'].replace(' ml', ''))
                beer.product_number = int(p['product_number'])
                db.session.add(beer)
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
manager.add_command('change_pass', changePass)
manager.add_command('add_default_roles', AddDefaultRoles)
manager.add_command('add_column_defaults', AddColumnDefaults)
manager.add_command('add_beers_from_json', AddBeersFromJson)



if __name__ == '__main__':
    manager.run()

