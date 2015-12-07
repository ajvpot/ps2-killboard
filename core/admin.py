# enable csrf validation on admin forms
from wtforms.csrf.session import SessionCSRF
from wtforms.meta import DefaultMeta
from flask import session, redirect, url_for, abort, request
from datetime import timedelta
from flask_admin import form
from flask_admin.contrib import sqla
from core import app
from flask_login import current_user

class SecureForm(form.BaseForm):
	class Meta(DefaultMeta):
		csrf = False # fix this later
		csrf_class = SessionCSRF
		csrf_secret = app.config['CSRF_SECRET']
		csrf_time_limit = timedelta(minutes=20)

	@property
	def csrf_context(self):
		return session

class SecureModelView(sqla.ModelView):
	form_base_class = SecureForm

	def is_accessible(self):
		if not current_user.is_active() or not current_user.is_authenticated():
			return False
		if current_user.access == 10:
			return True
		return False

	def _handle_view(self, name, **kwargs):
		"""
		Override builtin _handle_view in order to redirect users when a view is not accessible.
		"""
		if not self.is_accessible():
			if current_user.is_authenticated():
				abort(403)
			else:
				return redirect(url_for('login', next=request.url))
# initialize flask_admin
from core import admin
from wtforms.fields import SelectField
from core.models import db, DBUser

class UserView(SecureModelView):
	can_create = False
	column_exclude_list = ['password', 'salt']
admin.add_view(UserView(DBUser, db.session))
