from flask import render_template, redirect, url_for, flash, request
from flask_login import current_user, login_required
from .forms import NewProjectForm, DeleteForm, BrainstormForm, SetSectionsForm, EditSectionsForm
from werkzeug.security import check_password_hash 
from app.models import User, Project, Section
from wtforms import TextAreaField, StringField
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
			project = Project(title=form.title.data, user_id=current_user.id, stage=4)
		else:
			project = Project(title=form.title.data, user_id=current_user.id, stage=1)
		db.session.add(project)
		db.session.commit()

		return redirect(url_for('project.dashboard'))

	return render_template('project/new_project.html', form=form)

@project.route('/project_dashboard/<proj_id>', methods=['GET','POST'])
@login_required
def project_dashboard(proj_id):
	project = Project.query.get(int(proj_id))
	if current_user.id != project.user_id:
			return redirect(url_for('project.dashboard'))
	return render_template('project/project_dashboard.html', project=project, title='{}'.format(project.title))

@project.route('/brainstorm/<proj_id>', methods=['GET','POST'])
@login_required
def brainstorm(proj_id):
	project = Project.query.get(int(proj_id))
	if current_user.id != project.user_id:
			return redirect(url_for('project.dashboard'))
	form = BrainstormForm()
	if form.validate_on_submit():
		project.sources = form.sources.data
		project.freewrite = form.freewrite.data
		project.question = form.question.data
		sections = Section.query.filter_by(project_id=project.id).filter_by(parent_type='outline').order_by(Section.order)

		if form.num_sections.data < project.num_sections:
			difference = project.num_sections - form.num_sections.data
			rev_sections = Section.query.filter_by(project_id=project.id).filter_by(parent_type='outline').order_by(Section.order.desc())
			i = 0
			while i < difference:
				to_delete = rev_sections.first()
				db.session.delete(to_delete)
				i += 1

		elif form.num_sections.data > project.num_sections:
			difference = form.num_sections.data - project.num_sections
			i = project.num_sections + 1
			diff_counter = difference
			while diff_counter > 0:
				section = Section(
					project_id=project.id,
					parent_type="outline",
					order=sections.count()+1,
				)
				db.session.add(section)
				i += 1
				diff_counter -= 1
		else:
			pass		

		project.num_sections = form.num_sections.data
		project.thesis = form.thesis.data
		db.session.commit()
		flash('Brainstorm Saved', 'info')
		return redirect(url_for('project.project_dashboard', proj_id=project.id))
	return render_template('project/brainstorm.html', 
							project=project, 
							title='Brainstorm: {}'.format(project.title), 
							form=form,
							max_sections=15)

@project.route('/outline_editor/<proj_id>', methods=['GET', 'POST'])
@login_required
def outline_editor(proj_id):
	project = Project.query.get(int(proj_id))
	if current_user.id != project.user_id:
			return redirect(url_for('project.dashboard'))

	sections = Section.query.filter_by(project_id=project.id).filter_by(parent_type='outline').order_by(Section.order)

	class F(EditSectionsForm):
		pass

	num_sections = project.num_sections

	record = {}

	i = 1
	while i <= num_sections:
		record.update({'{}'.format(str(i)):'Section {}'.format(str(i))})
		i += 1
	
	for key, value in record.items():
		setattr(F, key, TextAreaField(value))

	form = F()

	if form.validate_on_submit():
		for key, value in record.items():
			section = sections.filter_by(order=key).first()
			data = getattr(form, key).data
			section.text = data

		db.session.commit()
		flash('Outline Saved', 'info')
		return redirect(url_for('project.project_dashboard', proj_id=project.id))

	return render_template(
		'project/outline_editor.html', 
		project=project, sections=sections, 
		form=form, 
		record=record,
		title='Outline: {}'.format(project.title)
	)

@project.route('/delete/type=<type>/id=<id>', methods=['GET', 'POST'])
@login_required
def delete(type, id):
	if type == 'project':
		project = Project.query.filter_by(id=id).first()
		if current_user.id != project.user_id:
			return redirect(url_for('project.dashboard'))
		item = Project.query.get(int(id))
	elif type == 'section':
		section = Section.query.get(int(id))
		if current_user.id != section.user_id:
			return redirect(url_for('project.dashboard'))
		item = section
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

