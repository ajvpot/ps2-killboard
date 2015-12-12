import pyximport
pyximport.install()
from orbit.framing import TEXT
from orbit.server import WebSocketResource
from orbit.transaction import Transaction, State, TransactionManager
from collections import deque
from core import app
from twisted.internet import reactor
from twisted.internet.defer import gatherResults
from core.formatters import characterinline, charactercell
import json

class ResolveState(State):
	def onNewConnection(self, ws):
		ws.opcode = TEXT
		ws.write(json.dumps({'type': 'status', 'msg': 'Subscribed'}))
		ws.write(json.dumps({'type': 'status', 'msg': 'Replay'}))
		for line in self.transaction.buffer:
			ws.write(line)
		ws.write(json.dumps({'type': 'status', 'msg': 'Live'}))

class ResolveTransaction(Transaction):
	buffer = deque(maxlen=250) # hopefully you dont subscribe to this much shit
	deferreds = []
	def subscribe(self, cacheResult):
		if cacheResult['resolved'] == True:
			return
		else:
			def _fix(ret):
				data = json.dumps({'id': ret[0], 'type': 'resolve', 'inline': str(characterinline(ret[1])), 'cell': str(charactercell(ret[1]))})
				self.buffer.append(data)
				self.sendUpdate(data)
			def printErr(ret):
				ret.printDetailedTraceback()
			self.deferreds.append(cacheResult['deferred'].addCallback(_fix).addErrback(printErr))
	def doneSubscribing(self):
		dl = gatherResults(self.deferreds)
		def _doneResolving(data, trans):
			reactor.callLater(5, trans.finish) # don't kill the transaction before the client connects
		dl.addCallback(_doneResolving, self)
		def _cleanup():
			try:
				self.finish()
			except:
				pass
		reactor.callLater(30, _cleanup) # timeout


transactionManager = TransactionManager()
resolveResource = WebSocketResource(transactionManager, 'subid') # subid is the get parameter