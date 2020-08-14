from flask import render_template, redirect, url_for, flash, request
from flask_login import current_user, login_user, logout_user
from werkzeug.urls import url_parse

from app.models import User
from app import db

from . import auth
from .forms import LoginForm, RegistrationForm

@auth.route('/login', methods=['GET','POST'])
def login():
	if current_user.is_authenticated:
		return redirect(url_for('home.home'))

	form = LoginForm()

	if form.validate_on_submit():
		user = User.query.filter_by(username=form.username.data).first()

		if user is None or not user.check_password(form.password.data):
			flash('Invalid Username or Password', 'danger')
			return redirect(url_for('auth.login'))

		flash('You are now signed in.', 'info')

		login_user(user, remember=form.remember_me.data)

		next_page = request.args.get('next')
		if not next_page or url_parse(next_page).netloc != '':
			next_page = url_for('home.home')
		
		return redirect(next_page)

	return render_template('auth/login.html', title='Sign In', form=form)

@auth.route('/logout')
def logout():
    logout_user()
    flash('You are now logged out.', 'info')
    return redirect(url_for('home.home'))

@auth.route('/register', methods=['GET', 'POST'])
def register():
	if current_user.is_authenticated:
		return redirect(url_for('home.home'))
	form = RegistrationForm()
	if form.validate_on_submit():
		user = User(username=form.username.data, email=form.email.data, first_name=form.first_name.data, last_name = form.last_name.data)
		user.set_password(form.password.data)
		db.session.add(user)
		db.session.commit()
		flash('You are now a registered user', 'success')
		return redirect(url_for('auth.login'))
	return render_template('auth/register.html', title='Register', form=form)


