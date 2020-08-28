from app import db, login
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from time import time
import jwt
from flask import current_app as app

@login.user_loader
def load_user(id):
	return User.query.get(int(id))

class User(db.Model, UserMixin):
	id = db.Column(db.Integer, primary_key=True)
	username = db.Column(db.String, unique=True)
	role = db.Column(db.String)
	email = db.Column(db.String, unique=True)
	first_name = db.Column(db.String)
	last_name = db.Column(db.String)
	password_hash = db.Column(db.String)
	timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
	projects = db.relationship('Project', backref='author', cascade="all,delete", lazy='dynamic')

	def set_password(self, password):
		self.password_hash = generate_password_hash(password)

	def check_password(self, password):
		return check_password_hash(self.password_hash, password)

	def get_reset_password_token(self, expires_in=600):
		return jwt.encode(
			{'reset_password': self.id, 'exp': time() + expires_in},
			app.config['SECRET_KEY'], algorithm='HS256').decode('utf-8')

	@staticmethod
	def verify_reset_password_token(token):
		try:
			id = jwt.decode(token, app.config['SECRET_KEY'],
							algorithms=['HS256'])['reset_password']
		except:
			return
		return User.query.get(id)

	def __repr__(self):
		return '<User {}>'.format(self.username)    

class Project(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
	title = db.Column(db.String)
	timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
	last_edit = db.Column(db.DateTime, index=True, default=datetime.utcnow)
	stage = db.Column(db.String)
	sources = db.Column(db.Text, default='')
	freewrite = db.Column(db.Text, default='')
	question = db.Column(db.Text, default='')
	thesis = db.Column(db.Text, default='')
	num_sections = db.Column(db.Integer, default=0)
	outline = db.Column(db.Text, default='')
	sections = db.relationship('Section', backref='project', cascade='all,delete', lazy='dynamic')
	drafts = db.Column(db.Integer, default=1)

	def __repr__(self):
		return '<Project {}>'.format(self.title)    

class Section(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	project_id = db.Column(db.Integer, db.ForeignKey('project.id'))
	label = db.Column(db.String)
	version = db.Column(db.Integer)
	parent_type = db.Column(db.String)
	order = db.Column(db.Integer)
	heading = db.Column(db.Text, default='')
	title = db.Column(db.Text, default='')
	text = db.Column(db.Text, default='')

	def __repr__(self):
		return '<Section {}>'.format(self.id)    