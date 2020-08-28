from flask import Flask, Blueprint, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager, current_user
from flask_bootstrap import Bootstrap
from flask_moment import Moment
from flask_mail import Mail
from flask_admin import Admin, AdminIndexView
from flask_admin.contrib.sqla import ModelView
import os


class MyAdminIndexView(AdminIndexView):
		def is_accessible(self):
			return current_user.is_authenticated and current_user.role == 'admin'

		def inaccessible_callback(self, name, **kwargs):
			# redirect to login page if user doesn't have access
			return redirect(url_for('error.nice_try'))

class UserModelView(ModelView):
	def is_accessible(self):
		return current_user.role == 'admin'

	def inaccessible_callback(self, name, **kwargs):
		# redirect to login page if user doesn't have access
		return redirect(url_for('error.nice_try'))

db = SQLAlchemy()
migrate = Migrate()
login = LoginManager()
login.login_view = 'auth.login'
login.login_message = 'Please log in to access this page.'
bootstrap = Bootstrap()
moment = Moment()
mail= Mail()

admin = Admin(index_view=MyAdminIndexView())
max_sections = 15

def create_app():
	app = Flask(__name__)
	app.config.from_object('config.Config')
	app.static_folder = 'static'

	# admin
	from app import models
	from .models import User, Section
	from .models import Project
	admin.init_app(app)
	#admin.add_view(UserModelView(User, db.session))

	# blueprints
	from .home import home as home_bp
	app.register_blueprint(home_bp)

	from .auth import auth as auth_bp
	app.register_blueprint(auth_bp, url_prefix='/auth')

	from .error import error as error_bp
	app.register_blueprint(error_bp)

	from .project import project as project_bp
	app.register_blueprint(project_bp, url_prefix='/project')

	app.config.update(dict(
		DEBUG = True,
		MAIL_SERVER = 'smtp.gmail.com',
		MAIL_PORT = 465,
		MAIL_USE_TLS = False,
		MAIL_USE_SSL = True,
		MAIL_USERNAME = os.environ.get('MAIL_USERNAME'),
		MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD'),
	))

	# extensions
	db.init_app(app)
	migrate.init_app(app, db)
	login.init_app(app)
	bootstrap.init_app(app)
	moment.init_app(app)
	mail.init_app(app)

	

	# logging
	if not app.debug and not app.testing:
		if app.config['LOG_TO_STDOUT']:
			stream_handler = logging.StreamHandler()
			stream_handler.setLevel(logging.INFO)
			app.logger.addHandler(stream_handler)
		else:
			if not os.path.exists('logs'):
				os.mkdir('logs')
			file_handler = RotatingFileHandler('logs/wrapp.log',
											   maxBytes=10240, backupCount=10)
			file_handler.setFormatter(logging.Formatter(
				'%(asctime)s %(levelname)s: %(message)s '
				'[in %(pathname)s:%(lineno)d]'))
			file_handler.setLevel(logging.INFO)
			app.logger.addHandler(file_handler)

		app.logger.setLevel(logging.INFO)
		app.logger.info('Wrapp startup')

	return app
