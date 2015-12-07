from core import app
from flask import Flask, session, request, flash, url_for, redirect, render_template, abort ,g
from flask.ext.login import login_user, logout_user, current_user, login_required
from core.models import DBUser, db
from core.util.wardenlogin import tryWardenLogin
from sqlalchemy.exc import IntegrityError

@app.errorhandler(IntegrityError)
def handleDBException(error):
	flash('That username or e-mail address already exists.', 'danger')
	return redirect(url_for('index'))

@app.route('/register', methods=['GET', 'POST'])
def register():
	if request.method == 'GET':
		return render_template('register.html')
	user = DBUser(request.form['username'], request.form['email'], request.form['password'])
	db.session.add(user)
	db.session.commit()
	flash('User successfully registered', 'success')
	return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
	if request.method == 'GET':
		return render_template('login.html')
	username = request.form['username']
	password = request.form['password']
	dbuser = DBUser.query.filter_by(username=username).filter_by(local=True).first()
	if dbuser is None or not dbuser.check_password(password):
		if tryWardenLogin(username, password):
			dbuser = DBUser.query.filter_by(username=username).filter_by(local=False).first()
			if dbuser is None:
				# create remote user
				dbuser = DBUser(username, "%s@warden.whitefire.in" % username, local=False)
				db.session.add(dbuser)
				db.session.commit()
				flash('Created local user account.', 'info')
			login_user(dbuser)
			flash('Logged in with Warden.', 'success')
			return redirect(request.args.get('next') or url_for('dashboard'))
		flash('Username or password is invalid', 'danger')
		return redirect(url_for('login'))
	login_user(dbuser)
	flash('Logged in successfully', 'success')
	return redirect(request.args.get('next') or url_for('dashboard'))

@app.route('/logout', methods=['GET', 'POST'])
def logout():
	logout_user()
	return redirect(url_for('index'))

@app.route('/test', methods=['GET', 'POST'])
@login_required
def testroute():
	return "ur logged in"