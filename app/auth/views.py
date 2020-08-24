from flask import render_template, redirect, url_for, flash, request
from flask_login import current_user, login_user, logout_user, login_required
from werkzeug.urls import url_parse
from werkzeug.security import check_password_hash

from wtforms.fields import Label

from app.models import User, Project
from app import db

from . import auth
from .forms import LoginForm, RegistrationForm, EditInfoForm, DeleteAccountForm, EditEmailForm, EditPasswordForm

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
			next_page = url_for('project.dashboard')
		
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
		flash('You are now a registered user.', 'success')
		return redirect(url_for('auth.login'))
	return render_template('auth/register.html', title='Register', form=form)


@auth.route('/account')
@login_required
def account():
	num_projects = Project.query.filter_by(user_id=current_user.id).count()
	return render_template('auth/account.html', title='Account', user=current_user, num_projects=num_projects)

@auth.route('/edit_info/?field=<field>', methods=['GET', 'POST'])
@login_required
def edit_info(field):
	form = EditInfoForm()
	if field == 'first_name':
		label = 'First Name'
	elif field == 'last_name':
		label = 'Last Name'
	elif field == 'username':
		label = 'Username'
	else:
		label = 'Info'
	form.field.label = Label(field_id = "name", text = label)
	if form.validate_on_submit():
		user = current_user
		setattr(user, field, form.field.data)

		db.session.commit()
		flash('Your information was saved.', 'success')
		return redirect(url_for('auth.account'))

	return render_template('auth/edit_info.html', title='Edit Info', user=current_user, form=form)

@auth.route('/edit_email', methods=['GET', 'POST'])
@login_required
def edit_email():
	form = EditEmailForm()
	if form.validate_on_submit():
		user = current_user
		user.email = form.email.data

		db.session.commit()
		flash('Your information was saved.', 'success')
		return redirect(url_for('auth.account'))

	return render_template('auth/edit_info.html', title='Edit Info', user=current_user, form=form)

@auth.route('/edit_password', methods=['GET', 'POST'])
@login_required
def edit_password():
	form = EditPasswordForm()
	if form.validate_on_submit():
		user = current_user
		if not user.check_password(form.old_password.data):
			flash('Wrong Password', 'danger')
			return redirect(url_for('auth.edit_password'))

		user.set_password(form.password.data)
		db.session.commit()
		flash('Your information was saved.', 'success')
		return redirect(url_for('auth.account'))

	return render_template('auth/edit_info.html', title='Edit Info', user=current_user, form=form)


@auth.route('/delete_account', methods=['GET', 'POST'])
@login_required
def delete_account():
	form = DeleteAccountForm()

	if form.validate_on_submit():
		user = current_user
		db.session.delete(user)
		db.session.commit()
		flash('Your account was deleted. Sorry to see you go!', 'info')
		return redirect(url_for('home.home'))

	return render_template('auth/delete_account.html', title='Delete Account', user=current_user, form=form)

