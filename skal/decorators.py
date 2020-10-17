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



def member_of_beernight(fn):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            # First check if user is authenticated.
            beer_id = kwargs['id']
            if not current_user.is_authenticated:
                return redirect(url_for('login'))
            beernightBeer = BeernightBeer.query.get(beer_id)
            beernight = Beernight.query.get(beernightBeer.beernight_id)
            is_member = beernight.is_user_member(current_user.id)
            if not is_member:
                flash("Ekki heimilað.", category="danger")
                return redirect(url_for('user.current_user_detail'))
            return fn(*args, **kwargs)
        return wrapper
    return decorator

