from flask_wtf import FlaskForm
from wtforms import SelectField


class Form(FlaskForm):
    missions = SelectField('missions', choices=[])