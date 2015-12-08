import core.startup as startup
from core import app
from flask import render_template, redirect, request, flash, abort, url_for, send_from_directory, jsonify
from flask.ext.login import login_required, current_user, fresh_login_required
from core.models import db
from datetime import timedelta
from datetime import datetime
import os
import requests
from core.ps2data import cache

@app.route('/')
def index():
	return render_template('index.html')

@app.route('/feed')
def feed():
	return render_template('feed.html')

@app.route('/dumpcache')
def dumpcache():
	return jsonify(cache=cache, buffer=list(startup.wsFactory.buffer))

@app.route('/lookup/<name>')
def lookup(name):
	name = name.lower()
	return requests.get("https://census.daybreakgames.com/s:vanderpot/get/ps2:v2/character/?name.first_lower=%s&c:show=character_id" % name).json()['character_list'][0]['character_id']

@app.route('/kpm')
def kpm():
	kt = startup.factory.listeners['kpm']
	return render_template('kpm.html', kt=kt, inaccurate=kt.inaccurate())

@app.route('/groupkill')
@app.route('/groupkill/<int:top>')
def groupkill(top=10):
	kt = startup.factory.listeners['groupkill']
	return render_template('groupkill.html', kt=kt, cache=cache, top=top)

