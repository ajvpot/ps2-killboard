from core.listeners.kpm import KPMTracker, KPMListener
import core.startup as startup
from core import app
from flask import render_template, redirect, request, flash, abort, url_for, send_from_directory, jsonify
from flask.ext.login import login_required, current_user, fresh_login_required
from core.models import db
from datetime import timedelta
from collections import defaultdict, OrderedDict
import operator
from core.formatters import resolveCharacterNames
from datetime import datetime
import time
import os
import requests
from core.ps2data import cache
from jinja2 import Template, Markup






@app.route('/')
def index():
	return render_template('index.html')

@app.route('/feed')
@app.route('/feed/<string:subid>')
def feed(subid="default"):
	return render_template('feed.html', kbid=subid)

@app.route('/dumpcache')
def dumpcache():
	return jsonify(cache=cache.cache)

@app.route('/lookup/<name>')
def lookup(name):
	name = name.lower()
	return requests.get("https://census.daybreakgames.com/s:vanderpot/get/ps2:v2/character/?name.first_lower=%s&c:show=character_id" % name).json()['character_list'][0]['character_id']

@app.route('/kpm')
def kpm():
	kt = startup.factory.listeners['kpm']

	return render_template('kpm.html',
	    kpm=kt,
	    tkkpm=startup.factory.listeners['tkkpm'],
	    suicidekpm=startup.factory.listeners['suicidekpm'],
	    esfcounter=startup.factory.listeners['esfcounter'],
		infantrykpm=startup.factory.listeners['infantrykpm'],
		sundererkpm=startup.factory.listeners['sundererkpm'],
		tankkpm=startup.factory.listeners['tankkpm'],
		harasserkpm=startup.factory.listeners['harasserkpm'],
		lightningkpm=startup.factory.listeners['lightningkpm'],
		libkpm=startup.factory.listeners['libkpm'],
		esfkpm=startup.factory.listeners['esfkpm'],
	    inaccurate=kt.inaccurate()
	)

@app.route('/stats/esfcounter')
def stats_esfcounter():
	return startup.factory.listeners['esfcounter'].csv()

@app.route('/stats/kpm/average/<tag>')
def stats_kpm(tag):
	tag = str(tag)
	if(tag in startup.factory.listeners and isinstance(startup.factory.listeners[tag], KPMListener)):
		return startup.factory.listeners[tag].csv()
	else:
		return 'Unknown tag',404

@app.route('/groupkill')
@app.route('/groupkill/<int:top>')
@resolveCharacterNames
def groupkill(top=10):
	kt = startup.factory.listeners['groupkill']
	return render_template('groupkill.html', kt=kt, cache=cache, top=top)

@app.route('/event')
@app.route('/event/')
def eventlist():
	return render_template('experiencelist.html', cache=cache)

@app.route('/event/<string:event>')
@app.route('/event/<string:event>/<int:top>')
@resolveCharacterNames
def simpleevent(event, top=10):
	kt = startup.factory.listeners['simpleevent']
	return render_template('simple.html', kt=kt, cache=cache, event=event, top=top)

@app.route('/playersearch', methods=['POST'])
def playerSearch():
	return redirect(url_for('player', cid=request.form.get('player')))

@app.route('/player/<cid>/')
@app.route('/player/<cid>')
@resolveCharacterNames
def player(cid):
	try:
		int(cid)
	except:
		r = requests.get('https://census.daybreakgames.com/s:vanderpot/get/ps2:v2/character/?name.first_lower=%s&c:show=character_id' % cid)
		try:
			newcid = r.json()['character_list'][0]['character_id']
		except IndexError:
			abort(404)
		return redirect(url_for('player', cid=newcid))
	return render_template('player.html', cid=cid, cache=cache) # ToDo: put cache in globals for jinja?

@app.route('/player/<cid>/kills')
@app.route('/player/<cid>/kills/')
@app.route('/player/<cid>/kills/<start>')
@app.route('/player/<cid>/kills/<start>/')
@resolveCharacterNames
def weaponMenu(cid, start=None):
	if start is None:
		start = int(time.time() - (60*60*24))
	else:
		start = int(start)
	r = requests.get('https://census.daybreakgames.com/s:vanderpot/get/ps2:v2/characters_event/?character_id=%s&c:limit=1000000&type=KILL' % cid)
	rd = r.json()
	if rd['returned'] == 0:
		abort(404)
	killlist = rd['characters_event_list']
	total = defaultdict(int)
	for kill in killlist:
		if int(kill['timestamp']) < start:
			continue
		if kill['attacker_character_id'] == kill['character_id']:
			continue
		total[kill['attacker_weapon_id']] += 1
	od = OrderedDict(sorted(total.items(), key=operator.itemgetter(1), reverse=True))


	return render_template('weaponmenu.html', total=od, cache=cache, cid=cid, start=start)

@app.route('/player/<cid>/kills/<weapon>/<start>')
@app.route('/player/<cid>/kills/<weapon>/<start>/')
@app.route('/player/<cid>/kills/<weapon>')
@app.route('/player/<cid>/kills/<weapon>/')
@resolveCharacterNames
def weaponStats(cid, weapon, start=None):
	if start is None:
		start = int(time.time() - (60*60*24))
	else:
		start = int(start)
	r = requests.get('https://census.daybreakgames.com/s:vanderpot/get/ps2:v2/characters_event/?character_id=%s&c:limit=1000000&type=KILL' % cid)
	rd = r.json()
	if rd['returned'] == 0:
		abort(404)
	killlist = rd['characters_event_list']
	all = []
	# ToDo: when a player gets a page with unresolved characters in it, make a websocket transaction and subscribe it to all pending resolve deferreds
	# ToDo: refactor character from dict to object?
	for kill in killlist:
		if int(kill['timestamp']) < start:
			continue
		if kill['attacker_character_id'] == kill['character_id']:
			continue
		if int(kill['attacker_weapon_id']) != int(weapon):
			continue
		all.append(kill)
	#trans.doneSubscribing() # ToDo
	od = sorted(all, key=lambda x: int(x['timestamp']), reverse=True)

	return render_template('weaponstats.html', total=od, cache=cache, cid=cid, start=start, weapon=weapon)