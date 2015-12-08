import time
from twisted.internet.defer import DeferredList
from core.ps2data import cache

esf_ids = ('7','8','9')

class ESFReservation(object):
	def __init__(self, name):
		self.name = name
		self.reserve = []
		self.wtf = 0

	def total(self):
		return len(self.reserve)

	def mark(self, characterid):
		if(not characterid in self.reserve):
			print '%s ESF Added (%s wtf) => %s' % (self.name, self.wtf, characterid)
			self.reserve.append(characterid)

	def remove(self, characterid, wtf=True):
		if(characterid in self.reserve):
			self.reserve.remove(characterid)
			print '%s ESF Removed (%s wtf) => %s' % (self.name, self.wtf, characterid)
		elif(wtf):
			self.wtf += 1
			print 'WTFFFF!?!?!?!?! %s' % (characterid)

	def __repr__(self):
		return '%s ESFs, %s wtf' % (len(self.reserve), self.wtf)

class ESFCounterListener(object):
	def __init__(self):
		self.track = {
			'nc': ESFReservation('nc'),
			'tr': ESFReservation('tr'),
			'vs': ESFReservation('vs'),
		}

	def csv(self):
		return '%s,%s,%s,%s' % (int(time.time()), self.track['vs'].total(), self.track['tr'].total(), self.track['nc'].total())

	def onMessage(self, payload):
		ids = ['5428308138483718321', '5428392193625290673']

		if(('character_id' in payload and payload['character_id'] in ids) or ('attacker_character_id' in payload and payload['attacker_character_id'] in ids)):
			print 'DEBUG DEBUG LOL: %s' % (repr(payload))

		if(payload['event_name'] == "VehicleDestroy"):
			if(not payload['vehicle_id'] in esf_ids and not payload['attacker_vehicle_id'] in esf_ids):
				return

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

			if(not attacker['resolved']):
				def _fix(data):
					results[1] = data[1]

				attacker['deferred'].addCallback(_fix)
				waiting.append(attacker['deferred'])

			def _finish(_=None):
				character,attacker = results

				if(payload['vehicle_id'] in esf_ids):
					self.track[cache.get('faction', payload['faction_id'])].remove(payload['character_id'])

				if(payload['attacker_vehicle_id'] in esf_ids):
					self.track[attacker['faction']].mark(payload['attacker_character_id'])

			if(len(waiting) >= 1):
				waiting = DeferredList(waiting)
				waiting.addCallback(_finish)
			else:
				_finish()
		elif(payload['event_name'] == 'Death'):
			if(not payload['attacker_vehicle_id'] in esf_ids):
				return

			attacker = cache.get('character', payload['attacker_character_id'])
			# we use a list here because the anonymous functions below can modify it
			results = [attacker]

			waiting = []

			if(not attacker['resolved']):
				def _fix(data):
					results[0] = data[1]

				attacker['deferred'].addCallback(_fix)
				waiting.append(attacker['deferred'])

			def _finish(_=None):
				attacker = results[0]

				self.track[attacker['faction']].mark(payload['attacker_character_id'])

			if(len(waiting) >= 1):
				waiting = DeferredList(waiting)
				waiting.addCallback(_finish)
			else:
				_finish()
		elif(payload['event_name'] == 'PlayerLogout'):
			for v in self.track.values():
				v.remove(payload['character_id'], wtf=False)