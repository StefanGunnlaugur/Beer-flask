from functools import wraps
import traceback

from flask import redirect, flash, url_for, request, render_template, Blueprint
from flask import current_app as app
from flask_security import login_required, roles_accepted, current_user
from skal.models import (Beernight, BeernightBeer)

def roles_accepted(roles):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for('login'))
            for r in roles:
                if current_user.has_role(r):
                    return f(*args, **kwargs)
            return redirect(url_for('user.current_user_detail'))
        return wrapper
    return decorator

def member_of_beernight(func):
    @wraps(func)
    def wrapper(beernight_id, *args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('login'))
        beernight = Beernight.query.get(beernight_id)
        is_member = beernight.is_user_member(current_user.id)
        if not is_member:
            flash("Ekki heimilað.", category="danger")
            return redirect(url_for('user.current_user_detail'))
        return func(beernight_id=beernight_id, *args, **kwargs)
    return wrapper

def not_member_of_beernight(func):
    @wraps(func)
    def wrapper(beernight_id, *args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('login'))
        beernight = Beernight.query.get(beernight_id)
        is_member = beernight.is_user_member(current_user.id)
        if is_member:
            flash("Ekki heimilað.", category="danger")
            return redirect(url_for('user.current_user_detail'))
        return func(beernight_id=beernight_id, *args, **kwargs)
    return wrapper

def admin_of_beernight(func):
    @wraps(func)
    def wrapper(beernight_id, *args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('login'))
        beernight = Beernight.query.get(beernight_id)
        is_admin = beernight.is_user_admin(current_user.id)
        if not is_admin:
            flash("Ekki heimilað.", category="danger")
            return redirect(url_for('user.current_user_detail'))
        return func(beernight_id=beernight_id, *args, **kwargs)
    return wrapper

def creator_of_beernight(func):
    @wraps(func)
    def wrapper(beernight_id, *args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('login'))
        beernight = Beernight.query.get(beernight_id)
        is_creator = beernight.is_user_creator(current_user.id)
        if not is_creator:
            flash("Ekki heimilað.", category="danger")
            return redirect(url_for('user.current_user_detail'))
        return func(beernight_id=beernight_id, *args, **kwargs)
    return wrapper

def member_of_or_public_beernight(func):
    @wraps(func)
    def wrapper(beernight_id, *args, **kwargs):
        beernight = Beernight.query.get(beernight_id)
        if beernight.is_public:
            return func(beernight_id=beernight_id, *args, **kwargs)
        if current_user.is_authenticated:
            is_member = beernight.is_user_member(current_user.id)
            if is_member:  
                return func(beernight_id=beernight_id, *args, **kwargs)
        flash("Ekki heimilað.", category="danger")
        return redirect(url_for('user.current_user_detail'))
    return wrapper
