from flask_mail import Message
from app import mail
from flask import render_template
from threading import Thread

from flask import current_app

def send_async_email(app, msg):
	with app.app_context():
		mail.send(msg)

def send_email(subject, sender, recipients, text_body, html_body):
	msg = Message(subject, sender=sender, recipients=recipients)
	msg.body = text_body
	msg.html = html_body
	Thread(target=send_async_email,
		   args=(current_app._get_current_object(), msg)).start()

def send_password_reset_email(user):
	token = user.get_reset_password_token()
	send_email('[Wriit] Reset Your Password',
			   sender='wrapp.admn@gmail.com',
			   recipients=[user.email],
			   text_body=render_template('email/reset_password.txt',
										 user=user, token=token),
			   html_body=render_template('email/reset_password.html',
										 user=user, token=token))

def export_draft_email(user, title, sections):
	send_email('[Wriit] Draft Export: {}'.format(title),
			   sender='wrapp.admn@gmail.com',
			   recipients=[user.email],
			   text_body=render_template('project/export_draft.txt',
										 sections=sections),
			   html_body=render_template('project/export_draft.html',
										 sections=sections))

