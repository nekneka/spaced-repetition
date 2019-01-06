from flask_security.forms import LoginForm, RegisterForm
from wtforms import StringField
from wtforms.validators import Optional, ValidationError
from src.models.users import User


class Login(LoginForm):

    def validate(self):
        response = super(Login, self).validate()
        return response


class Register(RegisterForm):
    username = StringField('Username (Optional)', [Optional()])

    def validate_username(self, field):
        user = User.query \
            .filter(User.username == field.data) \
            .all()
        if user:
            raise ValidationError('Sorry, this username is already taken')

    def validate(self):
        response = super(Register, self).validate()
        return response
