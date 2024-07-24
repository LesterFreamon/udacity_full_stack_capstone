from flask_security.forms import RegisterForm
from wtforms import SelectField, StringField
from wtforms.validators import DataRequired

class ExtendedRegisterForm(RegisterForm):
    username = StringField('Username', validators=[DataRequired()])
    role = SelectField('Role', choices=[('user', 'User'), ('admin', 'Admin')], validators=[DataRequired()])
