from core.websocket.killboard import transactionManager as killboardTransactionManager
import json
from core.ps2data import cache

class KillboardListener(object):
	def onMessage(self, payload):
		if(payload['event_name'] == "VehicleDestroy"):
			attacker = cache.get('character', payload['attacker_character_id'])

			if(not attacker['resolved']):
				def _fix(data):
					characterid, data = data
					self.broadcast(json.dumps({
						'type': 'resolve',
						'id': characterid,
						'data': data
					}))
					return (characterid,data)

				attacker['deferred'].addCallback(_fix)
				del attacker['deferred']

			self.broadcast(json.dumps({
				'type': 'parsed',
				'event_name': 'VehicleDestroy',
				'attacker': attacker,
				'attacker_weapon': cache.get('item', payload['attacker_weapon_id']),
				'vehicle': cache.get('vehicle', payload['vehicle_id']),
				'faction': cache.get('faction', payload['faction_id']),
			}))
		elif(payload['event_name'] == "Death"):
			character = cache.get('character', payload['character_id'])
			attacker = cache.get('character', payload['attacker_character_id'])

			if(not character['resolved']):
				def _fix(data):
					characterid, data = data
					self.broadcast(json.dumps({
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
					self.broadcast(json.dumps({
						'type': 'resolve',
						'id': characterid,
						'data': data
					}))
					return (characterid,data)

				attacker['deferred'].addCallback(_fix)
				del attacker['deferred']

			self.broadcast(json.dumps({
				'type': 'parsed',
				'event_name': 'Death',
				'character': character,
				'attacker': attacker,
				'attacker_weapon': cache.get('item', payload['attacker_weapon_id']),
			}))
	def broadcast(self, msg):
		for transaction in killboardTransactionManager.transactions.values():
			transaction.fromCensus(msg)