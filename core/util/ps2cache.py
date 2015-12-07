from collections import defaultdict
from twisted.python import log
from twisted.internet.defer import inlineCallbacks
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

class CharacterResolver(object):
	queue = []

	def __init__(self):
		log.msg("Initialized resolver", system="resolve")
		self.resolveRunner()

	def resolveRunner(self):
		if len(self.queue) == 0:
			reactor.callLater(app.config['PS2_QUERY_INTERVAL'], self.resolveRunner)
			return

		# remove dupes
		self.queue = list(set(self.queue))
		log.msg("Resolving %s character IDs" % len(self.queue), system="resolve")
		url = 'https://census.daybreakgames.com/s:vanderpot/get/ps2:v2/character/?character_id=%s&c:show=name.first,character_id,battle_rank.value,faction_id&c:resolve=outfit' % ','.join(self.queue)
		d = getPage(str(url))
		d.noisy = False
		self.queue = []

		def parseResolve(resp):
			#print resp
			list = json.loads(resp)['character_list']
			for character in list:
				try:
					disp = {'name': character['name']['first'],
							'id': character['character_id'],
							'br': character['battle_rank']['value'],
							'faction': cache.get('faction', character['faction_id']),
							'disp': '%s (%s)' % (character['name']['first'], character['battle_rank']['value']),
							'resolved': True}
					if 'outfit' in character.keys():
						disp['tag'] = character['outfit']['alias']
						disp['disp'] = "[%s] %s" % (disp['tag'], disp['disp'])

					self._broadcastResolve(character['character_id'], disp)
				except Exception as e:
					print "failed to broadcast, ", e
			reactor.callLater(app.config['PS2_QUERY_INTERVAL'], self.resolveRunner)

		def printErr(err):
			print "in resolverunner, ",err
			reactor.callLater(app.config['PS2_QUERY_INTERVAL'], self.resolveRunner)

		d.addCallback(parseResolve)
		d.addErrback(printErr)

	def _broadcastResolve(self, id, val):
		wsFactory.broadcast(json.dumps({
			'type': 'resolve',
			'id': id,
			'data': val
		}))

		cache.set('character', id, val) # ToDo: make this cache value a dict? resolve empire, br

	def resolve(self, characterid):
		cache.set('character', characterid, None)
		self.queue.append(characterid)

resolver = CharacterResolver()

class PS2Cache(object):
	cache = defaultdict(dict)
	hit = 0
	miss = 0

	def __init__(self):
		log.msg("Initialized cache", system="cache")
		lc = LoopingCall(self._statusReport)
		lc.start(15)

	def _statusReport(self):
		count = 0
		for dict in self.cache.values():
			count += len(dict.keys())

		log.msg('Cache contains %s keys, %s hit %s miss' % (count, self.hit, self.miss), system="cache")

	def get(self, type, key):
		if type == "character":
			if key in self.cache[type].keys() and self.cache[type][key] is not None:
				self.hit += 1

				return self.cache[type][key]
			else:
				resolver.resolve(key)
				self.miss += 1

				return {'resolved': False, 'name': key}
		else:
			if key in self.cache[type].keys():
				self.hit += 1
				return self.cache[type][key]
			else:
				self.miss += 1
				log.msg("CACHE MISS: [%s]%s" % (type, key), system="cache")

				return "CACHE MISS: key(%s)" % key # ToDo: Fix this

	def set(self, type, key, value):
		self.cache[type][key] = value


cache = PS2Cache()

#populate cache

log.msg("Populating item cache", system="cache")
cache.set('item', '0', 'Suicide')
d = getPage('https://census.daybreakgames.com/s:vanderpot/get/ps2:v2/item?item_type_id=26&c:limit=1000000&c:show=name.en,item_id')

def loadWeapons(resp):
	list = json.loads(resp)
	list = list['item_list']

	for item in list:
		try:
			cache.set('item', item['item_id'], item['name']['en'])
		except:
			pass

	log.msg("Item cache populated", system="cache")

def printErr(err):
	print err

d.addCallback(loadWeapons)
d.addErrback(printErr)

log.msg("Populating vehicle cache", system="cache")
d = getPage('https://census.daybreakgames.com/s:vanderpot/get/ps2:v2/vehicle?c:show=vehicle_id,name.en&c:limit=100000')

def loadWeapons(resp):
	list = json.loads(resp)
	list = list['vehicle_list']

	for vehicle in list:
		try:
			cache.set('vehicle', vehicle['vehicle_id'], vehicle['name']['en'])
		except:
			pass

	log.msg("Vehicle cache populated", system="cache")

def printErr(err):
	print err

d.addCallback(loadWeapons)
d.addErrback(printErr)

cache.set('faction', '2', 'nc')
cache.set('faction', '3', 'tr')
cache.set('faction', '1', 'vs')

cache.set('character', '0', {'name': 'Unknown',
							'id': 0,
							'br': 0,
							'faction': 'ns',
							'disp': 'Unknown',
							'resolved': True})
