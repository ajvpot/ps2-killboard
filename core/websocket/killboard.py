import pyximport
pyximport.install()
from orbit.framing import TEXT
from orbit.server import WebSocketResource
from orbit.transaction import Transaction, State, TransactionManager
from collections import deque
from core import app
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
		self.transaction.sendUpdate(data)

class KillboardTransaction(Transaction):
	buffer = deque(maxlen=100)
	def fromCensus(self, data):
		self.buffer.append(data)
		self.sendUpdate(data)


transactionManager = TransactionManager()

killboardResource = WebSocketResource(transactionManager, 'subid') # subid is the get parameter

transactionManager.addTransaction(KillboardTransaction(KillboardState()), 'default')