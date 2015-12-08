from autobahn.twisted.websocket import WebSocketClientProtocol, \
	WebSocketClientFactory
from twisted.internet import reactor, ssl
from autobahn.twisted.websocket import WebSocketClientFactory, \
    WebSocketClientProtocol, \
    connectWS
import json
from core import app
from twisted.python import log
from core.ps2data import cache

class PS2RealTimeClientProtocol(WebSocketClientProtocol):
	counter = 0

	def onConnect(self, response):
		print("Server connected: {0}".format(response.peer))

	def onOpen(self):

		print("WebSocket connection open.")

		self.sendMessage(json.dumps({'service': 'event',
									 'action': 'subscribe',
									 'characters': ['all'],
									 'eventNames': ['Death', 'VehicleDestroy', 'GainExperience']}))

		self.factory.receiver.ps2api = self

	def onMessage(self, payload, isBinary):
		self.counter += 1
		#self.factory.receiver.broadcast(payload)

		payload = json.loads(payload)

		if(not 'type' in payload or payload['type'] != 'serviceMessage'):
			return

		payload = payload['payload']

		if(app.config['PS2_FILTER_ENABLE']):
			try:
				if int(payload['attacker_character_id']) not in app.config['PS2_INTERESTED_IDS'] and int(payload['character_id']) not in app.config['PS2_INTERESTED_IDS']:
					#log.msg("Not interested in this message", system="census")
					return
				else:
					log.msg("Interested in this message", system="census")
			except Exception as e:
				log.msg("Failed to parse a thing %s" % e, system="census")

		# TODO: Refactor messages into objects with fetch methods for things that need to be resolved

		for x in self.factory.listeners.values():
			x.onMessage(payload)

		#print payload['event_name']
		if(payload['event_name'] == "VehicleDestroy"):
			attacker = cache.get('character', payload['attacker_character_id'])

			if(not attacker['resolved']):
				def _fix(data):
					characterid, data = data
					self.factory.receiver.broadcast(json.dumps({
						'type': 'resolve',
						'id': characterid,
						'data': data
					}))
					return (characterid,data)

				attacker['deferred'].addCallback(_fix)
				del attacker['deferred']

			self.factory.receiver.broadcast(json.dumps({
				'type': 'parsed',
				'event_name': 'VehicleDestroy',
				'attacker': attacker,
				'attacker_weapon': cache.get('item', payload['attacker_weapon_id']),
				'vehicle': cache.get('vehicle', payload['vehicle_id']),
				'faction': cache.get('faction', payload['faction_id']),
				'seq': self.counter
			}))
		elif(payload['event_name'] == "Death"):
			character = cache.get('character', payload['character_id'])
			attacker = cache.get('character', payload['attacker_character_id'])

			if(not character['resolved']):
				def _fix(data):
					characterid, data = data
					self.factory.receiver.broadcast(json.dumps({
						'type': 'resolve',
						'id': characterid,
						'data': data
					}))
					return (characterid,data)

				character['deferred'].addCallback(_fix)
				del character['deferred']

			if(not attacker['resolved']):
				def _fix(data):
					characterid, data = data
					self.factory.receiver.broadcast(json.dumps({
						'type': 'resolve',
						'id': characterid,
						'data': data
					}))
					return (characterid,data)

				attacker['deferred'].addCallback(_fix)
				del attacker['deferred']

			self.factory.receiver.broadcast(json.dumps({
				'type': 'parsed',
				'event_name': 'Death',
				'character': character,
				'attacker': attacker,
				'attacker_weapon': cache.get('item', payload['attacker_weapon_id']),
				'seq': self.counter
			}))

	def onClose(self, wasClean, code, reason):
		print("WebSocket connection closed: {0}".format(reason))