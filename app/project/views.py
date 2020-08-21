from flask import render_template, redirect, url_for, flash, request
from flask_login import current_user, login_required
from .forms import NewProjectForm, DeleteForm, OutlineForm, EditSectionsForm, LineEditorForm, SectionTextEditorForm, RenameProjectForm
from werkzeug.security import check_password_hash 
from app.models import User, Project, Section
from wtforms import TextAreaField, StringField
from app import db
from datetime import datetime

# for nlp
import spacy
import re
from collections import Counter
import numpy as np

from .analyzer import gen_hist, get_length_distribution, gen_bar
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
			project = Project(title=form.title.data, user_id=current_user.id, stage=4, timestamp=datetime.now())
		else:
			project = Project(title=form.title.data, user_id=current_user.id, stage=1, timestamp=datetime.now())
		db.session.add(project)
		db.session.commit()

		return redirect(url_for('project.project_dashboard', proj_id=project.id))

	return render_template('project/new_project.html', form=form, title='New Project')

@project.route('/project_dashboard/<proj_id>', methods=['GET','POST'])
@login_required
def project_dashboard(proj_id):
	project = Project.query.get(int(proj_id))
	if current_user.id != project.user_id:
		return redirect(url_for('project.dashboard'))
	return render_template('project/project_dashboard.html', project=project, title='{}'.format(project.title))

@project.route('/progress/<proj_id>')
@login_required
def progress(proj_id):
	project = Project.query.get(int(proj_id))
	if current_user.id != project.user_id:
		return redirect(url_for('project.dashboard'))

	stage = project.stage 
	project.stage = int(stage)+1
	db.session.commit()
	return redirect(url_for('project.project_dashboard', proj_id=project.id))

@project.route('rename_project/<proj_id>', methods=['GET', 'POST'])
@login_required
def rename_project(proj_id):
	project = Project.query.get(int(proj_id))
	if current_user.id != project.user_id:
		return redirect(url_for('project.dashboard'))
	
	form = RenameProjectForm()

	if form.validate_on_submit():
		project.title = form.title.data
		db.session.commit()
		flash('Project Renamed', 'success')
		return redirect(url_for('project.project_dashboard', proj_id=project.id))
	return render_template('project/rename_project.html', project=project, form=form)

@project.route('/outline/<proj_id>', methods=['GET','POST'])
@login_required
def outline(proj_id):
	project = Project.query.get(int(proj_id))
	if current_user.id != project.user_id:
		return redirect(url_for('project.dashboard'))
	form = OutlineForm()
	if form.validate_on_submit():
		project.sources = form.sources.data
		project.freewrite = form.freewrite.data
		project.question = form.question.data
		sections = Section.query.filter_by(project_id=project.id).filter_by(version=1).order_by(Section.order)

		if form.num_sections.data < project.num_sections:
			difference = project.num_sections - form.num_sections.data
			rev_sections = Section.query.filter_by(project_id=project.id).filter_by(version=1).order_by(Section.order.desc())
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
					parent_type="draft",
					version=1,
					order=sections.count()+1,
				)
				db.session.add(section)
				i += 1
				diff_counter -= 1
		else:
			pass		

		project.num_sections = form.num_sections.data
		project.thesis = form.thesis.data
		project.outline = form.outline.data
		project.last_edit = datetime.utcnow()
		db.session.commit()
		flash('Outline Saved', 'success')
		return redirect(url_for('project.project_dashboard', proj_id=project.id))
	return render_template('project/outline.html', 
							project=project, 
							title='Outline: {}'.format(project.title), 
							form=form,
							max_sections=15)

@project.route('/first_draft/<proj_id>', methods=['GET', 'POST'])
@login_required
def first_draft(proj_id):
	project = Project.query.get(int(proj_id))
	if current_user.id != project.user_id:
		return redirect(url_for('project.dashboard'))

	sections = Section.query.filter_by(project_id=project.id).filter_by(version=1).order_by(Section.order)
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
		project.last_edit = datetime.utcnow()
		db.session.commit()
		flash('First Draft Saved', 'success')
		return redirect(url_for('project.project_dashboard', proj_id=project.id))

	return render_template(
		'project/first_draft.html', 
		project=project, sections=sections, 
		form=form, 
		record=record,
		title='First Draft: {}'.format(project.title)
	)

@project.route('/draft_editor/<proj_id>/<version>', methods=['GET', 'POST'])
@login_required
def draft_editor(proj_id, version):
	project = Project.query.get(int(proj_id))
	if current_user.id != project.user_id:
		return redirect(url_for('project.dashboard'))
	sections = Section.query.filter_by(project_id=project.id).filter_by(version=version).all()

	return render_template('project/draft_editor.html', title='Draft Editor', project=project, sections=sections)

@project.route('/line_editor/<proj_id>/<section_id>', methods=['GET', 'POST'])
@login_required
def line_editor(proj_id, section_id):
	project = Project.query.get(int(proj_id))
	if current_user.id != project.user_id:
		return redirect(url_for('project.dashboard'))

	def cleanhtml(raw_html):
		cleanr = re.compile('<.*?>')
		cleantext = re.sub(cleanr, '', raw_html)
		return cleantext

	section = Section.query.get(int(section_id))
	if section.project.user_id != current_user.id:
		return redirect(url_for('project.dashboard'))


	nlp = spacy.load('en_core_web_sm')
	doc = nlp(cleanhtml(section.text))
	sentences = [sent for sent in doc.sents]
	
	form = LineEditorForm()

	for sentence in sentences:
		form.sentences.append_entry()

	combo = zip(sentences, form.sentences)
	
	if form.validate_on_submit():
		flash('Section Saved', 'success')
		compiled = ''
		for sentence in form.sentences:
			if sentence.data is not None:
				compiled += sentence.data + ' '
			section.text = compiled
			db.session.commit()

		return redirect(url_for('project.draft_editor', proj_id=project.id, version=1))

	return render_template('project/line_editor.html', 
							title='Line Editor', 
							sentences=sentences, 
							section=section,
							project=project, 
							combo=combo,
							form=form)
	
@project.route('/section_text_editor/<proj_id>/<section_id>', methods=['GET', 'POST'])
@login_required
def section_text_editor(proj_id, section_id):
	project = Project.query.get(int(proj_id))
	if current_user.id != project.user_id:
		return redirect(url_for('project.dashboard'))

	section = Section.query.get(int(section_id))
	if section.project.id != current_user.id:
		return redirect(url_for('project.dashboard'))

	form = SectionTextEditorForm()

	if form.validate_on_submit():
		section.text = form.text.data
		db.session.commit()
		flash('Section Saved', 'success')
		return redirect(url_for('project.draft_editor', proj_id=project.id, version=1))

	return render_template('project/section_text_editor.html', 
							title='Full Text Editor',
							section=section, 
							project=project, 
							form=form)

@project.route('/draft_viewer/<proj_id>')
@login_required
def draft_viewer(proj_id):
	project = Project.query.get(int(proj_id))
	if current_user.id != project.user_id:
		return redirect(url_for('project.dashboard'))
	
	sections = Section.query.filter_by(project_id=project.id).filter_by(version=1).all()

	return render_template('project/draft_viewer.html', project=project, sections=sections)
	
@project.route('/statistics/<proj_id>')
@login_required
def statistics(proj_id):
	project = Project.query.get(int(proj_id))
	if current_user.id != project.user_id:
		return redirect(url_for('project.dashboard'))

	def cleanhtml(raw_html):
		cleanr = re.compile('<.*?>')
		cleantext = re.sub(cleanr, '', raw_html)
		return cleantext

	sections=project.sections

	fulltext = ''
	for section in project.sections:
		fulltext += section.text + ' '

	nlp = spacy.load('en_core_web_sm')
	doc = nlp(cleanhtml(fulltext))

	#sentences
	sentences = [sent for sent in doc.sents]
	#all words
	words = [token.text for token in doc if token.is_punct != True]
	#minus stop words
	stop_words = [token.text for token in doc if token.is_stop != True and token.is_punct != True]
	#lemma
	lemma = [token.lemma_ for token in doc if token.is_stop != True and token.is_punct != True]
	#most common words
	word_freq = Counter(lemma)
	common_words = word_freq.most_common(10)

	sent_dist = get_length_distribution(sentences)
	word_dist = get_length_distribution(words)
	keyword_dist = get_length_distribution(lemma)
	print(common_words)

	#creating images
	hist = gen_hist(sent_dist)
	bar = gen_bar(common_words)

	data = {
		'Words': len(words),
		'Average Word Length (chars)': round(word_dist.mean(),2),
		'Longest Word (chars)': np.max(word_dist),
		'Sentences': len(sentences),
		'Average Sentence Length (words)': round(sent_dist.mean()),
		'Longest Sentence (words)': np.max(sent_dist),
		'Shortest Sentence (words)': np.min(sent_dist),
		'Double Spaced Pages': round(len(words)/250,2),
		'Single Spaced Pages': round(len(words)/500,2),
		'Reading Time': str(int(len(words)/300))+' minutes ' + str(int((len(words)/300)*60 % 60)) + ' seconds'
	}

	return render_template('project/analyzer.html', project=project, sections=sections, hist=hist, bar=bar, title='Statistics', data=data, common_words=common_words)

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