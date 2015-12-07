from core import app
import hashlib,random,string,time
from flask.ext.login import UserMixin
from flask.ext.sqlalchemy import SQLAlchemy
from sqlalchemy.dialects.mysql import *
from sqlalchemy.orm import relationship, backref

saltset = string.letters+string.digits

# uncomment for db support
db = SQLAlchemy(app)

class DBUser(db.Model, UserMixin):
	__tablename__ = 'users'
	id = db.Column(INTEGER(unsigned=True), primary_key=True)
	username = db.Column(VARCHAR(30), unique=True)
	email = db.Column(VARCHAR(255), unique=True)
	access = db.Column(SMALLINT(unsigned=True))
	password = db.Column(BINARY(20))
	local = db.Column(BOOLEAN())
	salt = db.Column(VARCHAR(10))
	joindate = db.Column(DATETIME())

	def __init__(self, username, email, password=None, salt=None, access=0, hash=True, account=None, token=None, local=True):
		self.username = username
		self.email = email
		if password:
			self.salt = salt if salt != None else ''.join([random.choice(saltset) for x in xrange(6)])

			if(not hash):
				self.password = password
			else:
				m = hashlib.sha1()
				m.update(self.salt + password)
				self.password = m.digest()
		self.local = local
		self.access = access
		self.joindate = time.strftime('%Y-%m-%d %H:%M:%S')

	def check_password(self, password):
		m = hashlib.sha1()
		m.update(self.salt + password)
		return m.digest() == self.password

	def change_password(self, password, newSalt=True):
		if newSalt:
			self.salt = ''.join([random.choice(saltset) for x in xrange(6)])
		m = hashlib.sha1()
		m.update(self.salt + password)
		self.password = m.digest()
		return

	def get_id(self):
		return unicode(self.id)

	def is_anonymous(self):
		return False

	def is_authenticated(self):
		return hasattr(self, 'id')

	def is_active(self):
		return hasattr(self, 'id')

	def __repr__(self):
		return '<User %r>' % self.username

