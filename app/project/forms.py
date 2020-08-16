from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, SelectField, TextAreaField, IntegerField, FieldList, Form, FormField
from wtforms.validators import  ValidationError, DataRequired, Email, EqualTo
from app.models import User, Project

class NewProjectForm(FlaskForm):
	title = StringField('Project Title', validators=[DataRequired()])
	progress = BooleanField('I already have a draft')
	submit = SubmitField('Create Project')

class DeleteForm(FlaskForm):
	password = PasswordField('Enter Your Password', validators=[DataRequired()])
	submit = SubmitField('Delete Project')

class BrainstormForm(FlaskForm):
	sources = TextAreaField('Sources')
	freewrite = TextAreaField('Freewrite')
	question = TextAreaField('Question')
	submit = SubmitField('Save')

class EditSectionsForm(FlaskForm):
	submit = SubmitField('Save')
	pass

class SetSectionsForm(FlaskForm):
	thesis = TextAreaField('Thesis')
	num_sections = IntegerField('Number of Sections')
	submit = SubmitField('Save')

class SectionForm(Form):
	heading = StringField("Heading")
	body = TextAreaField("Body")

class OutlineForm(FlaskForm):
	sections = FieldList(
		FormField(SectionForm),
		min_entries=1
	)




