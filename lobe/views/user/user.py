import traceback

from flask import redirect, flash, url_for, request, render_template, Blueprint
from flask import current_app as app
from flask_login import LoginManager, login_required, login_user, \
    logout_user, current_user, UserMixin

from sqlalchemy import or_

from lobe.decorators import roles_accepted
from lobe.models import User, Role, db, Beer, Beernight, BeernightInvitation
from lobe.db import resolve_order, make_beernight, make_beer
from lobe.forms import (UserEditForm, ExtendedRegisterForm, RoleForm, BeernightForm,
                        BeerForm)

user = Blueprint(
    'user', __name__, template_folder='templates')


@user.route('/users/')
@login_required
@roles_accepted(['admin'])
def user_list():
    page = int(request.args.get('page', 1))
    users = User.query.order_by(resolve_order(
                User,
                request.args.get('sort_by', default='name'),
                order=request.args.get('order', default='desc')))\
        .paginate(page, app.config['USER_PAGINATION'])
    return render_template(
        'user_list.jinja',
        users=users,
        section='admin')

@user.route('/admin/', methods=['GET', 'POST'])
@login_required
@roles_accepted(['admin'])
def admin_page():
    form = BeerForm(request.form)
    if request.method == 'POST':
        if form.validate():
            try:
                beer = make_beer(form)
                if beer:
                    flash("Tókst að búa til bjór {}.".format(
                                beer.name),
                                category="success")
                else:
                    flash(
                        "Ekki tókst að búa til bjór.",
                        category="warning")
            except Exception as error:
                print(error)
                flash(
                    "Ekki tókst að búa til bjór.",
                    category="warning")
        else:
            flash(
                "Ekki var fyllt rétt inn í reiti!",
                category="warning")
    return render_template(
        'admin.jinja',
        beerform=form,
        section='admin')

@user.route('/user/<int:id>/')
@login_required
@roles_accepted(['admin'])
def user_detail(id):
    user = User.query.get(id)
    return render_template(
        "user.jinja",
        user=user,
        section='user')

@user.route('/heimasida/', methods=['GET', 'POST'])
@login_required
@roles_accepted(['admin', 'Notandi'])
def current_user_detail():
    user = current_user
    form = BeernightForm(request.form)
    if request.method == 'POST':
        if form.validate():
            try:
                beernight = make_beernight(form, None, user)
                if beernight:
                    flash("Tókst að búa til bjórkvöld {}.".format(
                                beernight.name),
                                category="success")
                else:
                    flash(
                        "Ekki tókst að búa til bjórkvöld.",
                        category="warning")
            except Exception as error:
                print(error)
                flash(
                    "Ekki tókst að búa til bjórkvöld.",
                    category="warning")
        else:
            flash(
                "Ekki tókst að búa til bjórkvöld.",
                category="warning")
        return redirect(url_for('user.current_user_detail'))
    
    beernigts_member = sorted(user.beernights_member, key=lambda x: x.created_at, reverse=True)[:5]
    beernights_admin = sorted(user.beernights_admin, key=lambda x: x.created_at, reverse=True)[:5]
    invitations = sorted(user.invitations, key=lambda x: x.created_at, reverse=True)[:5]
    return render_template(
        "user.jinja",
        fav_beers = user.beers,
        beernights_member=beernigts_member,
        beernights_admin=beernights_admin,
        invites = invitations,
        beernight_form = form,
        user=user,
        section='user')

@user.route('/fav_beer_list/')
@login_required
@roles_accepted(['Notandi', 'admin'])
def fav_beer_list():
    page = int(request.args.get('page', 1))
    user = User.query.get(current_user.id)
    beers = Beer.query.filter(Beer.id.in_(user.beer_ids)).order_by(
            resolve_order(
                Beer,
                request.args.get('sort_by', default='created_at'),
                order=request.args.get('order', default='desc')))\
        .paginate(page, per_page=app.config['USER_TABLES_PAGINATION'])

    return render_template(
        'user_beers_list.jinja',
        beers=beers,
        section='user')

@user.route('/admin_beernight_list/')
@login_required
@roles_accepted(['Notandi', 'admin'])
def admin_beernight_list():
    page = int(request.args.get('page', 1))
    user = User.query.get(current_user.id)
    beernights = Beernight.query.filter(Beernight.id.in_(user.admin_beernight_ids)).order_by(
            resolve_order(
                Beernight,
                request.args.get('sort_by', default='created_at'),
                order=request.args.get('order', default='desc')))\
        .paginate(page, per_page=app.config['USER_TABLES_PAGINATION'])

    return render_template(
        'user_beernight_list_admin.jinja',
        beernights=beernights,
        section='user')

@user.route('/member_beernight_list/')
@login_required
@roles_accepted(['Notandi', 'admin'])
def member_beernight_list():
    page = int(request.args.get('page', 1))
    user = User.query.get(current_user.id)
    beernights = Beernight.query.filter(Beernight.id.in_(user.member_beernight_ids)).order_by(
            resolve_order(
                Beernight,
                request.args.get('sort_by', default='created_at'),
                order=request.args.get('order', default='desc')))\
        .paginate(page, per_page=app.config['USER_TABLES_PAGINATION'])

    return render_template(
        'user_beernight_list_member.jinja',
        beernights=beernights,
        section='user')


@user.route('/invites_list/')
@login_required
@roles_accepted(['Notandi', 'admin'])
def invites_list():
    page = int(request.args.get('page', 1))
    user = User.query.get(current_user.id)
    invites = BeernightInvitation.query.filter(BeernightInvitation.id.in_(user.invite_ids)).order_by(
            resolve_order(
                BeernightInvitation,
                request.args.get('sort_by', default='created_at'),
                order=request.args.get('order', default='desc')))\
        .paginate(page, per_page=app.config['USER_TABLES_PAGINATION'])

    return render_template(
        'user_invite_list.jinja',
        invites=invites,
        section='user')

@user.route('/users/<int:id>/edit/', methods=['GET', 'POST'])
@login_required
@roles_accepted(['admin'])
def user_edit(id):
    user = User.query.get(id)
    form = UserEditForm(obj=user)
    if request.method == 'POST':
        try:
            form = UserEditForm(request.form, obj=user)
            if form.validate():
                form.populate_obj(user)
                db.session.commit()
                flash("Notanda var breytt", category='success')
        except Exception as error:
            app.logger.error('Error updating a user : {}\n{}'.format(
                error, traceback.format_exc()))

    return render_template(
        'forms/model.jinja',
        user=user,
        form=form,
        type='edit',
        action=url_for('user.user_edit', id=id),
        section='user')


@user.route('/users/<int:id>/toggle_admin/', methods=['GET', 'POST'])
@login_required
@roles_accepted(['admin'])
def user_toggle_admin(id):
    ds_user = app.user_datastore.get_user(id)
    if ds_user.has_role('admin'):
        app.user_datastore.remove_role_from_user(ds_user, 'admin')
        app.user_datastore.add_role_to_user(ds_user, 'Notandi')
        flash("Notandi er ekki lengur vefstjóri", category='success')
    else:
        app.user_datastore.add_role_to_user(ds_user, 'admin')
        app.user_datastore.remove_role_from_user(ds_user, 'Notandi')
        flash("Notandi er nú vefstjóri", category='success')
    db.session.commit()
    return redirect(url_for('user.user_detail', id=id))


@user.route('/users/<int:id>/make_verifier/', methods=['GET', 'POST'])
@login_required
@roles_accepted(['admin'])
def user_make_verifier(id):
    ds_user = app.user_datastore.get_user(id)
    app.user_datastore.add_role_to_user(ds_user, 'Greinir')
    flash("Notandi er nú greinandi", category='success')
    db.session.commit()
    return redirect(url_for('user.user_detail', id=id))


@user.route('/users/create/', methods=['GET', 'POST'])
@login_required
@roles_accepted(['admin'])
def user_create():
    form = ExtendedRegisterForm(request.form)
    if request.method == 'POST' and form.validate():
        try:
            new_user = app.user_datastore.create_user(
                name=form.name.data,
                email=form.email.data,
                password=hash_password(form.password.data),
                roles=['admin' if form.is_admin.data else 'Notandi'])
            form.populate_obj(new_user)
            db.session.commit()
            flash("Nýr notandi var búinn til", category='success')
            return redirect(url_for('user.user_list'))
        except Exception as error:
            app.logger.error('Error creating a user : {}\n{}'.format(
                error, traceback.format_exc()))
            flash(
                "Villa kom upp við að búa til nýjan notanda",
                category='warning')
    return render_template(
        'forms/model.jinja',
        form=form,
        type='create',
        action=url_for('user.user_create'),
        section='user')



@user.route('/users/<int:id>/delete/')
@login_required
@roles_accepted(['admin'])
def delete_user(id):
    user = db.session.query(User).get(id)
    name = user.name
    db.session.delete(user)
    db.session.commit()
    flash("{} var eytt".format(name), category='success')
    return redirect(url_for('user.user_list'))


@user.route('/roles/create/', methods=['GET', 'POST'])
@login_required
@roles_accepted(['admin'])
def role_create():
    form = RoleForm(request.form)
    if request.method == 'POST' and form.validate():
        try:
            role = Role()
            form.populate_obj(role)
            db.session.add(role)
            db.session.commit()
        except Exception as error:
            app.logger.error('Error creating a role : {}\n{}'.format(
                error, traceback.format_exc()))
    return render_template(
        'forms/model.jinja',
        form=form,
        type='create',
        action=url_for('user.role_create'),
        section='role')


@user.route('/roles/<int:id>/edit/', methods=['GET', 'POST'])
@login_required
@roles_accepted(['admin'])
def role_edit(id):
    role = Role.query.get(id)
    form = RoleForm(request.form, obj=role)

    if request.method == 'POST' and form.validate():
        try:
            form.populate_obj(role)
            db.session.commit()
            flash("Hlutverki var breytt", category='success')
        except Exception as error:
            app.logger.error('Error updating a role : {}\n{}'.format(
                error, traceback.format_exc()))
    return render_template(
        'forms/model.jinja',
        role=role,
        form=form,
        type='edit',
        action=url_for('user.role_edit', id=id),
        section='role')
