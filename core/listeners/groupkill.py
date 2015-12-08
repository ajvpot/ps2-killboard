from twisted.internet.defer import DeferredList
from twisted.internet.task import LoopingCall
from core.ps2data import cache
from twisted.python import log
from twisted.internet import reactor
import time
from core.ps2data import cache
from collections import defaultdict, OrderedDict

TIMEOUT = 1
THRESHOLD = 3

class GroupKillStreak(object):
	def __init__(self, pid, tracker):
		self.pid = pid
		self.tracker = tracker
		self.total = 0
		reactor.callLater(TIMEOUT, self._finalize)

	def _finalize(self):
		if self.total < THRESHOLD:
			return
		if self.tracker.groupkills[self.pid] > self.total:
			return
		else:
			self.tracker.groupkills[self.pid] = self.total
			cache.get('character', self.pid) # Populate cache so the webpage can use it
		del self.tracker.active[self.pid]

	def mark(self):
		self.total += 1

class GroupKillTracker(object):
	def __init__(self):
		self.groupkills = defaultdict(int)
		self.active = {}

	def _getStreak(self, pid):
		if not pid in self.active.keys():
			self.active[pid] = GroupKillStreak(pid, self)
			return self.active[pid]
		else:
			return self.active[pid]

	def mark(self, pid):
		self._getStreak(pid).mark()

	def top(self, top=10):
		od = OrderedDict(sorted(self.groupkills.items(), key=lambda x: x[1], reverse=True))
		return od.items()[:top]

	def __repr__(self):
		return 'GroupKillTracker'

class GroupKillListener(object):
	def __init__(self):
		self.tracker = GroupKillTracker()
		self.started = time.time()

		l = LoopingCall(self.status)
		#l.start(5.0)

	def status(self):
		log.msg(repr(self.tracker.groupkills), system="GroupKillListener")

	def onMessage(self, payload):
		if(payload['event_name'] == "Death"):
			self.tracker.mark(payload['attacker_character_id'])