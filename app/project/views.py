from flask import render_template, redirect, url_for, flash, request
from flask_login import current_user, login_required
from .forms import NewProjectForm, DeleteForm
from werkzeug.security import check_password_hash 
from app.models import User, Project, Section
from app import db

from . import project

@project.route('/dashboard')
@login_required
def dashboard():
	projects = current_user.projects.all()
	return render_template('project/dashboard.html', projects=projects, title='Dashboard')

@project.route('/new_project', methods=['GET', 'POST'])
@login_required
def new_project():
	form = NewProjectForm()

	if form.validate_on_submit():
		if form.progress.data == True:
			project = Project(title=form.title.data, user_id=current_user.id, stage=2)
		else:
			project = Project(title=form.title.data, user_id=current_user.id, stage=1)
		db.session.add(project)
		db.session.commit()

		return redirect(url_for('project.dashboard'))

	return render_template('project/new_project.html', form=form)

@project.route('/drafter/<proj_id>', methods=['GET', 'POST'])
@login_required
def drafter(proj_id):
	project = Project.query.get(int(proj_id))
	if current_user.id != project.user_id:
			return redirect(url_for('project.dashboard'))
	
	return render_template('project/drafter.html', project=project, title='Drafter')

@project.route('/editor/<proj_id>', methods=['GET', 'POST'])
@login_required
def editor(proj_id):
	project = Project.query.get(int(proj_id))
	if current_user.id != project.user_id:
			return redirect(url_for('project.dashboard'))
	
	return render_template('project/editor.html', project=project, title='Editor')

@project.route('/delete/type=<type>/id=<id>', methods=['GET', 'POST'])
@login_required
def delete(type, id):
	if type == 'project':
		project = Project.query.filter_by(id=id).first()
		if current_user.id != project.user_id:
			return redirect(url_for('project.dashboard'))
		item = Project.query.get(int(id))
	elif type == 'idea':
		idea = Idea.query.get(int(id))
		if current_user.id != idea.user_id:
			return redirect(url_for('project.dashboard'))
		item = Project.query.get(int(id))
	elif type == 'outline':
		outline = Outline.query.get(int(id))
		if current_user.id != outline.user_id:
			return redirect(url_for('project.dashboard'))
		item = Project.query.get(int(id))
	elif type == 'draft':
		draft = Draft.query.get(int(id))
		if current_user.id != draft.user_id:
			return redirect(url_for('project.dashboard'))
		item = Project.query.get(int(id))
	else:
		return redirect(url_for('project.dashboard'))

	form = DeleteForm()

	if form.validate_on_submit():
		if check_password_hash(current_user.password_hash, form.password.data):
			db.session.delete(item)
			db.session.commit()
			flash('Deleted Successfully', 'info')
			return redirect(url_for('project.dashboard'))

		else:
			flash('Password Incorrect', 'danger')

	return render_template('project/delete.html', item=item, form=form, title='Delete')

