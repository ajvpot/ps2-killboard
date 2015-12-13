import time
from twisted.internet import reactor
from twisted.internet.defer import DeferredList
from core.ps2data import cache
from twisted.python import log

esf_ids = ('7','8','9')

class ESFReservation(object):
	def __init__(self, name):
		self.name = name
		self.reserve = []
		self.removelater = {}
		self.wtf = 0

	def total(self):
		return len(self.reserve)

	def mark(self, characterid):
		if(not characterid in self.reserve):
			# log.msg('%s ESF Added   (%s wtf) => %s' % (self.name, self.wtf, characterid), system="esfcounter")
			self.reserve.append(characterid)

			if(characterid in self.removelater):
				self.removelater[characterid].cancel()
				self.removelater[characterid] = reactor.callLater(60*2, self.remove, characterid, False)

	def remove(self, characterid, wtf=True):
		if(characterid in self.reserve):
			self.reserve.remove(characterid)
			# log.msg('%s ESF Removed (%s wtf) => %s' % (self.name, self.wtf, characterid), system="esfcounter")

			if(characterid in self.removelater):
				try:
					self.removelater[characterid].cancel()
				except:
					pass

				del self.removelater[characterid]
		elif(wtf):
			self.wtf += 1
			# log.msg('%s ESF WTF!!!! (%s wtf) => %s' % (self.name, self.wtf, characterid), system="esfcounter")

	# def __repr__(self):
	# 	return '%s ESFs, %s wtf' % (len(self.reserve), self.wtf)

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