import os
import traceback

from flask import (redirect, url_for, render_template, send_from_directory,
                   flash, request, Blueprint)
from flask import current_app as app
from flask_security import current_user, login_required

main = Blueprint(
    'main', __name__,
    template_folder='templates',
    static_folder='static',
    static_url_path='/main/static')


@main.route('/')
@login_required
def index():
    if current_user.has_role('Notandi'):
        return redirect(url_for('user_page'))
    return redirect(url_for('beer.beer_list'))




@main.errorhandler(404)
def page_not_found(error):
    flash("Við fundum ekki síðuna sem þú baðst um.", category="warning")
    return redirect(url_for('index'))


@main.errorhandler(500)
def internal_server_error(error):
    flash("Alvarleg villa kom upp, vinsamlega reynið aftur", category="danger")
    app.logger.error('Server Error: %s', (error))
    return redirect(url_for('index'))


@main.route('/not-in-chrome/')
def not_in_chrome():
    return render_template(
        'not_in_chrome.jinja',
        previous=request.args.get('previous'))
