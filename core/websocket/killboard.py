import pyximport
pyximport.install()
from twisted.internet.defer import inlineCallbacks
from orbit.framing import TEXT
from flask import Flask, render_template, request, session
from orbit.server import WebSocketResource, WSGISiteResource
from orbit.transaction import Transaction, State, TransactionManager
from twisted.web.static import File
from twisted.internet import reactor
from twisted.web.server import Site
from twisted.web.wsgi import WSGIResource
from twisted.python import log
from twisted.web.resource import Resource
from collections import deque
import cgi, urlparse, os, sys

class KillboardState(State):
	def __init__(self, filter=None):
		self.filter = filter
		return

	def onNewConnection(self, ws):
		ws.opcode = TEXT
		#for line in self.transaction.buffer:
		#	self.ws.write(str(line))

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

transaction = KillboardTransaction(KillboardState())
transactions = [transaction]
print transactionManager.addTransaction(transaction, 'default')