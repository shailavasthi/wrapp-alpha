from flask import render_template, redirect, url_for, flash, request, json
from flask_login import current_user, login_required
from .forms import NewProjectForm, DeleteForm, OutlineForm, EditSectionsForm, LineEditorForm, SectionTextEditorForm, RenameProjectForm
from werkzeug.security import check_password_hash 
from app.models import User, Project, Section
from wtforms import TextAreaField, StringField
from app import db, max_sections
from datetime import datetime
from app.email import export_draft_email

# for nlp
import spacy
import re
from collections import Counter
import numpy as np
import textstat

from .analyzer import get_length_distribution, get_reading_level
from . import project

import math

@project.route('/dashboard')
@login_required
def dashboard():
	projects = current_user.projects.order_by(Project.last_edit.desc()).all()
	return render_template('project/dashboard.html', projects=projects, title='Dashboard')

@project.route('/new_project', methods=['GET', 'POST'])
@login_required
def new_project():
	form = NewProjectForm()

	if form.validate_on_submit():
		project = Project(title=form.title.data, user_id=current_user.id, stage=1, timestamp=datetime.utcnow())
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
		sections = Section.query.filter_by(project_id=project.id).order_by(Section.order)

		if form.num_sections.data < project.num_sections:
			difference = project.num_sections - form.num_sections.data
			rev_sections = Section.query.filter_by(project_id=project.id).order_by(Section.order.desc())
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
					order=sections.count()+1,
					title='Section ' + str(sections.count()+1)
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
							max_sections=max_sections)

@project.route('/first_draft/<proj_id>', methods=['GET', 'POST'])
@login_required
def first_draft(proj_id):
	project = Project.query.get(int(proj_id))
	if current_user.id != project.user_id:
		return redirect(url_for('project.dashboard'))

	sections = Section.query.filter_by(project_id=project.id).order_by(Section.order)
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

@project.route('/draft_editor/<proj_id>', methods=['GET', 'POST'])
@login_required
def draft_editor(proj_id):
	project = Project.query.get(int(proj_id))
	if current_user.id != project.user_id:
		return redirect(url_for('project.dashboard'))
	sections = Section.query.filter_by(project_id=project.id).order_by(Section.order).all()


	return render_template('project/draft_editor.html', title='Draft Editor', project=project, sections=sections)

@project.route('new_section/<proj_id>', methods=['GET', 'POST'])
@login_required
def new_section(proj_id):
	project = Project.query.get(int(proj_id))
	if current_user.id != project.user_id:
		return redirect(url_for('project.dashboard'))
	
	if project.sections.count() <= max_sections:
		new_section_order = Section.query.filter_by(project_id=project.id).order_by(Section.order.desc()).first().order + 1
		section = Section(
			project_id=project.id,
			order=new_section_order,
			title='Section ' + str(new_section_order)
		)
		db.session.add(section)
		db.session.commit()
		return redirect(url_for('project.draft_editor', proj_id=project.id))
	else:
		flash('Maximum number of sections reached', 'info')
		return redirect(url_for('project.draft_editor', proj_id=project.id))


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
		project.last_edit = datetime.utcnow()
		compiled = ''
		for sentence in form.sentences:
			if sentence.data is not None:
				compiled += sentence.data + ' '
			section.text = compiled
			section.title = form.title.data
			db.session.commit()

		return redirect(url_for('project.draft_editor', proj_id=project.id))

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
	if section.project.user_id != current_user.id:
		return redirect(url_for('project.dashboard'))

	form = SectionTextEditorForm()

	if form.validate_on_submit():
		project.last_edit = datetime.utcnow()
		section.title = form.title.data
		section.text = form.text.data
		db.session.commit()
		flash('Section Saved', 'success')
		return redirect(url_for('project.draft_editor', proj_id=project.id))

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
	
	sections = Section.query.filter_by(project_id=project.id).order_by(Section.order).all()

	return render_template('project/draft_viewer.html', project=project, sections=sections)

@project.route('/export_draft/<proj_id>')
@login_required
def export_draft(proj_id):
	project = Project.query.get(int(proj_id))
	if current_user.id != project.user_id:
		return redirect(url_for('project.dashboard'))
	sections = Section.query.filter_by(project_id=project.id).order_by(Section.order).all()
	export_draft_email(current_user, project.title, sections)
	flash('Your draft was sent to your email. Check your spam folder if it is missing.', 'info')
	return redirect(url_for('project.draft_editor', proj_id=project.id))

	
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
	fulltext = cleanhtml(fulltext)
	nlp = spacy.load('en_core_web_sm')
	doc = nlp(fulltext)

	#sentences
	sentences = [sent for sent in doc.sents]
	#all words
	words = [token.text for token in doc if token.is_punct != True]
	#lemma
	lemma = [token.lemma_ for token in doc if token.is_stop != True and token.is_punct != True]
	#most common words
	word_freq = Counter(lemma)
	common_words = word_freq.most_common(10)
	
	sent_dist = get_length_distribution(sentences)
	word_dist = get_length_distribution(words)
	keyword_dist = get_length_distribution(lemma)

	def roundup(x):
		return int(math.ceil(x / 10.0))*10

	sent_hist, sent_bins = np.histogram(sent_dist, range=(0,roundup(sent_dist.max())))
	sent_hist=sent_hist.tolist()
	sent_bins=[str(round(label, 2)) for label in sent_bins.tolist()]
	sent_hist = ['Frequency']+sent_hist

	word_hist, word_bins = np.histogram(word_dist, range=(0,roundup(word_dist.max())))
	word_hist=word_hist.tolist()
	word_bins=[str(round(label, 2)) for label in word_bins.tolist()]
	word_hist = ['Frequency']+word_hist

	common_word_labels = []
	common_word_counts = ['Count']

	for label, count in common_words:
		common_word_labels.append(label)
		common_word_counts.append(count)

	flesch_score = textstat.flesch_reading_ease(fulltext)
	
	reading_level = get_reading_level(flesch_score)
	
	data = {
		'Words': len(words),
		'Average Word Length (letters)': round(word_dist.mean(),2),
		'Longest Word (letters)': np.max(word_dist),
		'Sentences': len(sentences),
		'Average Sentence Length (words)': round(sent_dist.mean()),
		'Longest Sentence (words)': np.max(sent_dist),
		'Shortest Sentence (words)': np.min(sent_dist),
		'Double Spaced Pages': round(len(words)/250,2),
		'Single Spaced Pages': round(len(words)/500,2),
		'Reading Time': str(int(len(words)/300))+' minutes ' + str(int((len(words)/300)*60 % 60)) + ' seconds',
		'Reading Level': reading_level,
	}

	return render_template('project/analyzer.html', 
							project=project, 
							sections=sections, 
							title='Statistics', 
							data=data, 
							common_words=common_words,
							sent_hist=json.dumps(sent_hist),
							sent_bins=json.dumps(sent_bins),
							word_hist=json.dumps(word_hist),
							word_bins=json.dumps(word_bins),
							common_word_labels=json.dumps(common_word_labels),
							common_word_counts=json.dumps(common_word_counts)
						)

@project.route('/delete/<type>/<id>', methods=['GET', 'POST'])
@login_required
def delete(type, id):
	if type == 'project':
		project = Project.query.filter_by(id=id).first()
		next_page = url_for('project.dashboard')
		if current_user.id != project.user_id:
			return redirect(url_for('project.dashboard'))
		item = Project.query.get(int(id))
	elif type == 'section':
		section = Section.query.get(int(id))
		next_page = url_for('project.draft_editor', proj_id=section.project.id)
		if current_user.id != section.project.user_id:
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
			return redirect(next_page)

		else:
			flash('Password Incorrect', 'danger')

	return render_template('project/delete.html', item=item, form=form, title='Delete')