import os

from flask_security.forms import LoginForm, RegisterForm
from flask_wtf import RecaptchaField, FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms import (Form, HiddenField, MultipleFileField, SelectMultipleField,
                     SelectField, TextField, BooleanField, validators,
                     ValidationError, FloatField, widgets, StringField)

from wtforms.ext.sqlalchemy.fields import QuerySelectField
from wtforms.ext.sqlalchemy.orm import model_form
from wtforms.fields.html5 import EmailField
from wtforms.validators import InputRequired
from wtforms_alchemy import ModelForm
from wtforms_components import IntegerField

from lobe.models import (Role, User, Beer, db)


class MultiCheckboxField(SelectMultipleField):
    """
    A multiple-select, except displays a list of checkboxes.

    Iterating the field will produce subfields, allowing custom rendering of
    the enclosed checkbox fields.
    """
    widget = widgets.ListWidget(prefix_label=False)
    option_widget = widgets.CheckboxInput()


class BeerEditForm(ModelForm):
    class Meta:
        model = Beer
        # exclude = ['is_synth']


class ExtendedLoginForm(LoginForm):
    if not os.getenv("FLASK_ENV", 'development') == 'development':
        recaptcha = RecaptchaField()


class ExtendedRegisterForm(RegisterForm):
    name = TextField(
        'Nafn',
        [validators.required()])
    sex = SelectField(
        'Kyn',
        [validators.required()],
        choices=[
            ('Kona', 'Kona'),
            ('Karl', 'Karl'),
            ('Annað', 'Annað')])
    age = IntegerField(
        'Aldur',
        [
            validators.required(),
            validators.NumberRange(min=18, max=100)])
    is_admin = BooleanField("Notandi er vefstjóri")


RoleForm = model_form(
    model=Role,
    base_class=Form,
    db_session=db.session)



class UserEditForm(Form):
    name = TextField('Nafn')
    email = TextField('Netfang')
    sex = SelectField(
        'Kyn',
        [validators.required()],
        choices=[
            ('Kona', 'Kona'),
            ('Karl', 'Karl'),
            ('Annað', 'Annað')])
    age = IntegerField('Aldur')




