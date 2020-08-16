from app import db, login
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

@login.user_loader
def load_user(id):
    return User.query.get(int(id))

class User(db.Model, UserMixin):
	id = db.Column(db.Integer, primary_key=True)
	username = db.Column(db.String, unique=True)
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

	def __repr__(self):
		return '<User {}>'.format(self.username)    

class Project(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
	title = db.Column(db.String)
	timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
	stage = db.Column(db.String)
	sources = db.Column(db.Text, default='')
	freewrite = db.Column(db.Text, default='')
	question = db.Column(db.Text, default='')
	thesis = db.Column(db.Text, default='')
	num_sections = db.Column(db.Integer, default=0)
	sections = db.relationship('Section', backref='project', cascade='all,delete', lazy='dynamic')

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
	text = db.Column(db.Text, default='')