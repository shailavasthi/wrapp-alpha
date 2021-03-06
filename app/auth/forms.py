from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import  ValidationError, DataRequired, Email, EqualTo
from app.models import User

class LoginForm(FlaskForm):
	username = StringField('Username', validators=[DataRequired()])
	#email = StringField('Email', validators=[DataRequired()])
	password = PasswordField('Password', validators=[DataRequired()])
	remember_me = BooleanField('Remember Me')
	submit = SubmitField('Submit')


class RegistrationForm(FlaskForm):
	first_name=StringField('First Name', validators=[DataRequired()])
	last_name=StringField('Last Name', validators=[DataRequired()])
	username = StringField('Username', validators=[DataRequired()])
	email = StringField('Email', validators=[DataRequired(), Email()])
	password = PasswordField('Password', validators=[DataRequired()])
	password2 = PasswordField(
		'Repeat Password', validators=[DataRequired(), EqualTo('password')])
	submit = SubmitField('Register')

	def validate_username(self, username):
		user = User.query.filter_by(username=username.data).first()
		if user is not None:
			raise ValidationError('Please use a different username.')

	def validate_email(self, email):
		user = User.query.filter_by(email=email.data).first()
		if user is not None:
			raise ValidationError('Please use a different email address.')

class EditInfoForm(FlaskForm):
	field=StringField(validators=[DataRequired()])
	submit = SubmitField('Save Info')

class EditEmailForm(FlaskForm):
	email=StringField('Email', validators=[DataRequired(), Email()])
	submit = SubmitField('Save Email')

class EditPasswordForm(FlaskForm):
	old_password = PasswordField('Current Password', validators=[DataRequired()])
	password = PasswordField('New Password', validators=[DataRequired()])
	password2 = PasswordField(
		'Repeat New Password', validators=[DataRequired(), EqualTo('password')])
	submit = SubmitField('Save Password')

class DeleteAccountForm(FlaskForm):
	password = PasswordField('Confirm your password', validators=[DataRequired()])
	submit = SubmitField('Delete Account')

class ResetPasswordRequestForm(FlaskForm):
	email = StringField('Email', validators=[DataRequired(), Email()])
	submit = SubmitField('Request Password Reset')

class ResetPasswordForm(FlaskForm):
	password = PasswordField('Password', validators=[DataRequired()])
	password2 = PasswordField(
		'Repeat Password', validators=[DataRequired(), EqualTo('password')])
	submit = SubmitField('Request Password Reset')