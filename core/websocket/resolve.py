import pyximport
pyximport.install()
from orbit.framing import TEXT
from orbit.server import WebSocketResource
from orbit.transaction import Transaction, State, TransactionManager
from collections import deque
from core import app
from twisted.internet import reactor
from twisted.internet.defer import gatherResults
import json

class ResolveState(State):
	def onNewConnection(self, ws):
		ws.opcode = TEXT
		ws.write(json.dumps({'type': 'status', 'msg': 'Subscribed'}))
		for line in self.transaction.buffer:
			ws.write(line)

class ResolveTransaction(Transaction):
	buffer = deque(maxlen=250) # hopefully you dont subscribe to this much shit
	deferreds = []
	def subscribe(self, cacheResult):
		if cacheResult['resolved'] == True:
			return
		else:
			def _fix(ret):
				data = json.dumps({'id': ret[0], 'type': 'resolve', 'data': ret[1]})
				self.buffer.append(data)
				self.sendUpdate(data)
			self.deferreds.append(cacheResult['deferred'].addCallback(_fix))
	def doneSubscribing(self):
		dl = gatherResults(self.deferreds)
		def doneResolving(data, trans):
			print "done resolving"
			reactor.callLater(5, trans.finish) # don't kill the transaction before the client connects
		dl.addCallback(doneResolving, self)
		reactor.callLater(30, self.finish) # timeout


transactionManager = TransactionManager()
resolveResource = WebSocketResource(transactionManager, 'subid') # subid is the get parameter