from twisted.internet.defer import DeferredList
from twisted.internet.task import LoopingCall
from core.ps2data import cache
import time

class KPMMinute(object):
	def __init__(self, t):
		self.ts = t
		self.total = 0

	def mark(self):
		self.total += 1

class KPMTracker(object):
	def __init__(self):
		self.hour = []

	def _clean(self):
		if(len(self.hour) < 1):
			return

		newest = self.hour[-1].ts

		# purge entries older than an hour
		for x in self.hour[0:]:
			if(newest - x.ts > 60):
				self.hour.remove(x)

	def mark(self):
		self._clean()

		m = int(time.time() / 60)

		# if we have no entries or we're newer than the last newest entry
		if(len(self.hour) < 1 or m > self.hour[-1].ts):
			add = KPMMinute(m)
			add.mark()
			self.hour.append(add)
		else: # otherwise we're equal to the newest entry
			self.hour[-1].mark()

	def total(self, clean=True):
		self._clean()
		return float(sum([x.total for x in self.hour]))

	def average(self, clean=True):
		self._clean()
		return float(sum([x.total for x in self.hour])) / 60.0

	def totalAndAverage(self, clean=True):
		if(clean):
			self._clean()

		return self.total(), self.average()

	def __repr__(self):
		return '%s average with %s total' % self.totalAndAverage()

class KPMListener(object):
	def __init__(self):
		self.kills = {
			'tr': KPMTracker(),
			'nc': KPMTracker(),
			'vs': KPMTracker(),
		}
		self.started = time.time()

		l = LoopingCall(self.status)
		l.start(5.0)

	# returns true if we haven't had over an hour of stats yet
	def inaccurate(self):
		return (time.time()-self.started) < 3600

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

			if(not attacker['resolved']):
				def _fix(data):
					results[1] = data[1]

				attacker['deferred'].addCallback(_fix)
				waiting.append(attacker['deferred'])

			def _finish(_=None):
				character,attacker = results

				if(attacker['faction'] != character['faction']):
					if(attacker['faction'] in self.kills):
						self.kills[attacker['faction']].mark()

			if(len(waiting) >= 1):
				waiting = DeferredList(waiting)
				waiting.addCallback(_finish)
			else:
				_finish()