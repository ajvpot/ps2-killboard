import pyximport
pyximport.install()
from orbit.framing import TEXT
from orbit.server import WebSocketResource
from orbit.transaction import Transaction, State, TransactionManager
from collections import deque
import json

class KillboardState(State):
	def __init__(self, filter=None):
		self.filter = filter
		return

	def onNewConnection(self, ws):
		ws.opcode = TEXT
		ws.write(json.dumps({'type': 'status', 'msg': '* Playback start'}))
		for line in self.transaction.buffer:
			ws.write(str(line))
		ws.write(json.dumps({'type': 'status', 'msg': '* Playback complete'}))

	def onUpdate(self, ws, opcode, data, fin):
		print data
		self.transaction.sendUpdate(data)

class KillboardTransaction(Transaction):
	buffer = deque(maxlen=100)
	def fromCensus(self, data):
		if not hasattr(self, 'filter'):
			self.filter = None
		if(self.filter != None):
			if(not self.filter(data)):
				return
		self.buffer.append(data)
		self.sendUpdate(data)


transactionManager = TransactionManager()

killboardResource = WebSocketResource(transactionManager, 'subid') # subid is the get parameter

print transactionManager.addTransaction(KillboardTransaction(KillboardState()), 'default')