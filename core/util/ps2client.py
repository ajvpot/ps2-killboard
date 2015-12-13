from autobahn.twisted.websocket import WebSocketClientProtocol
import json
from core import app
import copy
from twisted.python import log
from core.ps2data import cache

class PS2RealTimeClientProtocol(WebSocketClientProtocol):
	counter = 0

	def onConnect(self, response):
		log.msg("Server connected: {0}".format(response.peer), system="census")

	def onOpen(self):

		log.msg("WebSocket connection open.", system="census")

		self.sendMessage(json.dumps({'service': 'event',
									 'action': 'subscribe',
									 'world': '17', # emerald
									 'characters': ['all'],
									 'eventNames': ['Death', 'VehicleDestroy', 'GainExperience', 'PlayerLogin', 'PlayerLogout']}))

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
			x.onMessage(copy.deepcopy(payload))

		#print payload['event_name']

	def onClose(self, wasClean, code, reason):
		log.msg("WebSocket connection closed: {0}".format(reason), system="census")