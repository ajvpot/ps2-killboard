from core.ps2data import cache
import json
from twisted.internet.defer import DeferredList



class Message(object):
	def __init__(self, payload):
		self.payload = payload

	def pullData(self):
		waiting = []

		for x in self.resolve:
			x = x.split('|')
			item = cache.get(x[1], self.payload[x[0]])

			if(item['resolved']):
				self.payload[x[0]] = item
			else:
				def _fix(data):
					self.payload[x[0]] = data[1]
					return data

				item['deferred'].addCallback(_fix)
				waiting.append(item['deferred'])

		if(len(waiting) > 0):
			return DeferredList(waiting)
		else:
			return None

class DeathMessage(Message):
	event_name = "Death"
	resolve = ['character_id|character', 'attacker_character_id|character']

	def __repr__(self):
		return "<DeathMessage, attacker=%s, character=%s>" % (self.payload['attacker_character_id'], self.payload['character_id'])

class VehicleDestroyMessage(Message):
	event_name = "VehicleDestroy"
	resolve = ['character_id|character', 'attacker_character_id|character']

	def __repr__(self):
		return "<VehicleDestroy, attacker=%s, vehicle=%s>" % (self.payload['attacker_character_id'], self.payload['vehicle_id'])

messageMap = {'Death': DeathMessage,
			  'VehicleDestroy': VehicleDestroyMessage,
			  # ToDo: add all event types
			  }

def messageFromCensus(payload):
	if payload['event_name'] in messageMap.keys():
		return messageMap[payload['event_name']](payload)
	else:
		return None