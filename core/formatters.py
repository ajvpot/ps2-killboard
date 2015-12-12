from core.ps2data import cache
from jinja2 import Template, Markup
from core import app
from flask import request, url_for, g


def charactercell(char):
	# takes a character cache result
	if char['resolved'] == True:
		t = Template("""
		<td class="faction {{ char['faction'] }}" data-cid="{{ char['id'] }}"><a href="/player/{{ char['id'] }}">[{{ char['tag'] }}] {{ char['name'] }} ({{ char['br'] }})</a></td>
		""")
		return Markup(t.render(char=char, url_for=url_for))
	else:
		t = Template("""
		<td class="loading" data-cid="{{ id }}">{{ id }}</td>
		""")
		if hasattr(request, 'resolveTrans'):
			request.resolveTrans.subscribe(char)
		return Markup(t.render(id=char['id']))
app.jinja_env.globals['charactercell'] = charactercell

def characterinline(char):
	# takes a character cache result
	if char['resolved'] == True:
		t = Template("""
		<span data-cid="{{ char['id'] }}"><a href="/player/{{ char['id'] }}">[{{ char['tag'] }}] {{ char['name'] }} ({{ char['br'] }})</a></td>
		""")
		return Markup(t.render(char=char, url_for=url_for))
	else:
		t = Template("""
		<span class="loading" data-cid="{{ id }}">{{ id }}</span>
		""")
		if hasattr(request, 'resolveTrans'):
			request.resolveTrans.subscribe(char)
		return Markup(t.render(id=char['id']))
app.jinja_env.globals['characterinline'] = characterinline

@app.after_request
def finishSubscribing(response):
	if hasattr(request, 'resolveTrans'):
		request.resolveTrans.doneSubscribing()
		print "done sub"
	return response

from functools import wraps
from flask import request

def resolveCharacterNames(func):
	@wraps(func)
	def decorated_function(*args, **kwargs):
		from core.websocket.resolve import transactionManager as resolveTransactionManager
		from core.websocket.resolve import ResolveTransaction, ResolveState
		request.resolveTrans = ResolveTransaction(ResolveState())
		request.resolveSubid = resolveTransactionManager.addTransaction(request.resolveTrans)
		return func(*args, **kwargs)

	return decorated_function