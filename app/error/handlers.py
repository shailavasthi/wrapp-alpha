from flask import render_template
from app import db
from . import error

@error.app_errorhandler(404)
def not_found_error(error):
	print('error 404 triggered')
	return render_template('error/404.html', title='404'), 404

@error.app_errorhandler(500)
def internal_error(error):
	db.session.rollback()
	return render_template('error/500.html', title='500'), 500