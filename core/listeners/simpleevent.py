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

def getEventDict():
	return defaultdict(int)

class SimpleEventTracker(object):
	def __init__(self):
		self.events = defaultdict(getEventDict)

	def mark(self, event, pid):
		self.events[event][pid] += 1

	def top(self, event, top=10):
		od = OrderedDict(sorted(self.events[event].items(), key=lambda x: x[1], reverse=True))
		return od.items()[:top]

	def __repr__(self):
		return 'SimpleEventTracker'

class SimpleEventListener(object):
	def __init__(self):
		self.tracker = SimpleEventTracker()
		self.started = time.time()

		l = LoopingCall(self.status)
		#l.start(5.0)

	def status(self):
		log.msg(repr(self.tracker.events), system="GroupKillListener")

	def onMessage(self, payload):
		if(payload['event_name'] == "GainExperience"):
			self.tracker.mark(payload['experience_id'], payload['character_id'])