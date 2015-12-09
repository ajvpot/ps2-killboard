from collections import defaultdict
from twisted.python import log
from twisted.internet.defer import inlineCallbacks, Deferred
import json
from twisted.internet import reactor
from twisted.internet.task import LoopingCall
from twisted.web.client import getPage
from twisted.internet import reactor
from sys import getsizeof, stderr
from itertools import chain
from collections import deque
from core import app

try:
	from reprlib import repr
except ImportError:
	pass

_debugging = False

class CharacterResolver(object):
	def __init__(self, query_interval, batch_max=200):
		# map of character_id: [list of deferreds for people waiting on id information]
		self.queue = {}
		self.batch_max = batch_max

		# RETARDED CIRCULAR REFERENCE LOL todo
		self.cache = None

		self.loop = LoopingCall(self.resolveRunner)
		self.loop.start(query_interval)

	def stop(self):
		self.loop.stop()

	def resolveRunner(self):
		if(len(self.queue) == 0):
			return

		if(_debugging):
			log.msg("Resolving %s character IDs" % len(self.queue), system="resolve")

		q = self.queue.keys()[0:self.batch_max]

		url = 'https://census.daybreakgames.com/s:vanderpot/get/ps2:v2/character/?character_id=%s&c:show=name.first,character_id,battle_rank.value,faction_id&c:resolve=outfit' % ','.join(q)
		d = getPage(str(url))
		d.noisy = False

		def parseResolve(resp):
			l = json.loads(resp)['character_list']

			for character in l:
				disp = {
					'name': character['name']['first'],
					'id': character['character_id'],
					'br': character['battle_rank']['value'],
					# RETARDED CIRCULAR REFERENCE LOL todo
					'faction': self.cache.get('faction', character['faction_id']),
					'disp': '%s (%s)' % (character['name']['first'], character['battle_rank']['value']),
					'resolved': True
				}

				if 'outfit' in character.keys():
					disp['tag'] = character['outfit']['alias']
					disp['disp'] = "[%s] %s" % (disp['tag'], disp['disp'])

				for d in self.queue[character['character_id']]:
					d.callback((character['character_id'], disp))

				del self.queue[character['character_id']]

		def printErr(err):
			log.msg("ERR: in resolverunner, %r" % (err))
			#reactor.stop()

		d.addCallback(parseResolve)
		d.addErrback(printErr)

	def _broadcastResolve(self, id, val):
		for d in self.queue[id]:
			d.callback(val)

		del self.queue[id]

		# wsFactory.broadcast(json.dumps({
		# 	'type': 'resolve',
		# 	'id': id,
		# 	'data': val
		# }))

		# cache.set('character', id, val) # ToDo: make this cache value a dict? resolve empire, br

	def resolve(self, characterid):
		# cache.set('character', characterid, None)
		d = Deferred()

		if(characterid in self.queue):
			self.queue[characterid].append(d)
		else:
			self.queue[characterid] = [d]

		return d

class PS2Cache(object):
	cache = defaultdict(dict)
	hit = 0
	miss = 0

	def __init__(self, resolver):
		if(_debugging):
			log.msg("Initialized cache", system="cache")

		self.resolver = resolver
		# RETARDED CIRCULAR REFERENCE LOL todo
		self.resolver.cache = self

		if(_debugging):
			lc = LoopingCall(self._statusReport)
			lc.start(15)

	def _statusReport(self):
		count = 0

		for dict in self.cache.values():
			count += len(dict.keys())

		if(_debugging):
			log.msg('Cache contains %s keys, %s hit %s miss' % (count, self.hit, self.miss), system="cache")

	def get(self, type, key):
		if type == "character":
			if key in self.cache[type].keys() and self.cache[type][key] is not None:
				self.hit += 1

				return self.cache[type][key]
			else:
				def _fix(data):
					self.set('character', *data) #characterid, data
					return data

				d = self.resolver.resolve(key)
				d.addCallback(_fix)
				self.miss += 1

				return {'resolved': False, 'name': key, 'id': key, 'deferred': d}
		else:
			if key in self.cache[type].keys():
				self.hit += 1

				return self.cache[type][key]
			else:
				self.miss += 1

				if(_debugging):
					log.msg("CACHE MISS: [%s]%s" % (type, key), system="cache")

				return "CACHE MISS: key(%s)" % key # ToDo: Fix this

	def set(self, type, key, value):
		self.cache[type][key] = value

	# this is semi-retarded, yolo
	def populate(self):
		if(_debugging):
			log.msg("Populating item cache", system="cache")

		self.set('item', '0', 'Suicide')
		d = getPage('https://census.daybreakgames.com/s:vanderpot/get/ps2:v2/item?item_type_id=26&c:limit=1000000&c:show=name.en,item_id')

		def loadWeapons(resp):
			list = json.loads(resp)
			list = list['item_list']

			for item in list:
				try:
					self.set('item', item['item_id'], item['name']['en'])
				except:
					pass

			if(_debugging):
				log.msg("Item cache populated", system="cache")

		def printErr(err):
			print err

		d.addCallback(loadWeapons)
		d.addErrback(printErr)

		if(_debugging):
			log.msg("Populating vehicle cache", system="cache")

		d = getPage('https://census.daybreakgames.com/s:vanderpot/get/ps2:v2/vehicle?c:show=vehicle_id,name.en&c:limit=100000')

		def loadWeapons(resp):
			list = json.loads(resp)
			list = list['vehicle_list']

			for vehicle in list:
				try:
					self.set('vehicle', vehicle['vehicle_id'], vehicle['name']['en'])
				except:
					pass

			if(_debugging):
				log.msg("Vehicle cache populated", system="cache")

		def printErr(err):
			print err

		d.addCallback(loadWeapons)
		d.addErrback(printErr)

		if(_debugging):
			log.msg("Populating experience", system="cache")

		d = getPage('https://census.daybreakgames.com/s:vanderpot/get/ps2:v2/experience?c:limit=1000')

		def loadExperience(resp):
			list = json.loads(resp)
			list = list['experience_list']

			for event in list:
				try:
					self.set('experience', event['experience_id'], event['description'])
				except:
					pass

			if(_debugging):
				log.msg("Experience cache populated", system="cache")

		def printErr(err):
			print err

		d.addCallback(loadExperience)
		d.addErrback(printErr)

		self.set('faction', '2', 'nc')
		self.set('faction', '3', 'tr')
		self.set('faction', '1', 'vs')

		self.set('character', '0', {'name': 'Unknown',
									'id': 0,
									'br': 0,
									'faction': 'ns',
									'disp': 'Unknown',
									'resolved': True})
