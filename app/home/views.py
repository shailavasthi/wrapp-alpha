from flask import render_template
from . import home as home_bp

@home_bp.route('/')
def home():
	return render_template('home/index.html', title='Home')

@home_bp.route('/donate')
def donate():
	return render_template('home/donate.html', title='Donate')