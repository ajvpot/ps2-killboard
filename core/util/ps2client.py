
from autobahn.twisted.websocket import WebSocketClientProtocol, \
	WebSocketClientFactory
from core.util.websocket import wsFactory
from twisted.internet import reactor, ssl
from autobahn.twisted.websocket import WebSocketClientFactory, \
    WebSocketClientProtocol, \
    connectWS
import json
from core import app
from twisted.python import log
from core.util.ps2cache import cache
class MyClientProtocol(WebSocketClientProtocol):
	counter = 0
	def onConnect(self, response):
		print("Server connected: {0}".format(response.peer))

	def onOpen(self):

		print("WebSocket connection open.")

		self.sendMessage(json.dumps({'service': 'event',
									 'action': 'subscribe',
									 'characters': ['all'],
									 'eventNames': ['Death', 'VehicleDestroy']}))
		self.factory.receiver.ps2api = self

	def onMessage(self, payload, isBinary):
		self.counter += 1
		#self.factory.receiver.broadcast(payload)
		try:
			payload = json.loads(payload)
			if payload['type'] != 'serviceMessage':
				return
			payload = payload['payload']

			if app.config['PS2_FILTER_ENABLE']:
				try:
					if int(payload['attacker_character_id']) not in app.config['PS2_INTERESTED_IDS'] and int(payload['character_id']) not in app.config['PS2_INTERESTED_IDS']:
						#log.msg("Not interested in this message", system="census")
						return
					else:
						log.msg("Interested in this message", system="census")
				except Exception as e:
					log.msg("Failed to parse a thing %s" % e, system="census")


			#print payload['event_name']
			if payload['event_name'] == "VehicleDestroy":
				self.factory.receiver.broadcast(json.dumps({
					'type': 'parsed',
					'event_name': 'VehicleDestroy',
					'attacker': cache.get('character', payload['attacker_character_id']),
					'attacker_weapon': cache.get('item', payload['attacker_weapon_id']),
					'vehicle': cache.get('vehicle', payload['vehicle_id']),
					'faction': cache.get('faction', payload['faction_id']),
					'seq': self.counter
				}))
			elif payload['event_name'] == "Death":
				self.factory.receiver.broadcast(json.dumps({
					'type': 'parsed',
					'event_name': 'Death',
					'character': cache.get('character', payload['character_id']),
					'attacker': cache.get('character', payload['attacker_character_id']),
					'attacker_weapon': cache.get('item', payload['attacker_weapon_id']),
					'seq': self.counter
				}))
		except Exception as e:
			log.msg("Failed to decode a message, %s" % e, system="census")


	def onClose(self, wasClean, code, reason):
		print("WebSocket connection closed: {0}".format(reason))


factory = WebSocketClientFactory(u"wss://push.planetside2.com/streaming?environment=ps2&service-id=s:vanderpot", debug=True)
factory.protocol = MyClientProtocol
factory.receiver = wsFactory

contextFactory = ssl.ClientContextFactory()

connectWS(factory, contextFactory)