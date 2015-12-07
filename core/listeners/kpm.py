from twisted.internet.defer import DeferredList
from twisted.internet.task import LoopingCall
from core.ps2data import cache

class KPMListener(object):
	def __init__(self):
		self.kills = {
			'tr': 0,
			'nc': 0,
			'vs': 0,
		}

		l = LoopingCall(self.status)
		l.start(5.0)

	def status(self):
		print repr(self.kills)

	def onMessage(self, payload):
		if(payload['event_name'] == "Death"):
			character = cache.get('character', payload['character_id'])
			attacker = cache.get('character', payload['attacker_character_id'])
			# we use a list here because the anonymous functions below can modify it
			results = [character, attacker]

			waiting = []

			if(not character['resolved']):
				def _fix(data):
					results[0] = data[1]

				character['deferred'].addCallback(_fix)
				waiting.append(character['deferred'])

			if(not attacker['resolved'])    :
				def _fix(data):
					results[1] = data[1]

				attacker['deferred'].addCallback(_fix)
				waiting.append(attacker['deferred'])

			def _finish(_=None):
				character,attacker = results

				if(attacker['faction'] != character['faction']):
					self.kills[attacker['faction']] += 1

			if(len(waiting) >= 1):
				waiting = DeferredList(waiting)
				waiting.addCallback(_finish)
			else:
				_finish()