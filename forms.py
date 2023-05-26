from flask_wtf import  FlaskForm
from wtforms import SubmitField, SelectField,FloatField
from flask_wtf.recaptcha import RecaptchaField

class MyForm(FlaskForm):
    recaptcha = RecaptchaField()
    submit = SubmitField('Submit')

class FloatForm(FlaskForm):
    float_number = FloatField('Float')