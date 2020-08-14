from flask import Flask, Blueprint
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_bootstrap import Bootstrap


db = SQLAlchemy()
migrate = Migrate()
login = LoginManager()
login.login_view = 'auth.login'
login.login_message = 'Please log in to access this page.'
bootstrap = Bootstrap()

def create_app():
	app = Flask(__name__)
	app.config.from_object('config.Config')
	app.static_folder = 'static'

	from app import models

	from .home import home as home_bp
	app.register_blueprint(home_bp)

	from .auth import auth as auth_bp
	app.register_blueprint(auth_bp, url_prefix='/auth')

	from .error import error as error_bp
	app.register_blueprint(error_bp)

	from .project import project as project_bp
	app.register_blueprint(project_bp, url_prefix='/project')

	db.init_app(app)
	migrate.init_app(app, db)
	login.init_app(app)
	bootstrap.init_app(app)

	return app
