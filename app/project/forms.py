from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, SelectField, TextAreaField, IntegerField, FieldList, Form, FormField
from wtforms.validators import  ValidationError, DataRequired, Email, EqualTo
from app.models import User, Project

class NewProjectForm(FlaskForm):
	title = StringField('Project Title', validators=[DataRequired()])
	progress = BooleanField('I already have a draft')
	submit = SubmitField('Create Project')

class RenameProjectForm(FlaskForm):
	title = StringField('Project Title', validators=[DataRequired()])
	submit = SubmitField('Rename Project')

class DeleteForm(FlaskForm):
	password = PasswordField('Enter Your Password', validators=[DataRequired()])
	submit = SubmitField('Delete Project')

class OutlineForm(FlaskForm):
	sources = TextAreaField('Sources')
	freewrite = TextAreaField('Freewrite')
	question = TextAreaField('Question')
	thesis = TextAreaField('Thesis')
	outline = TextAreaField('Outline')
	num_sections = IntegerField('Number of Sections')
	submit = SubmitField('Save Outline')

class EditSectionsForm(FlaskForm):
	submit = SubmitField('Save Draft')
	pass

class LineEditorForm(FlaskForm):
	sentences = FieldList(TextAreaField('Sentence'))
	submit = SubmitField('Save Section')

class SectionTextEditorForm(FlaskForm):
	text = TextAreaField('Text')
	submit = SubmitField('Save Section')