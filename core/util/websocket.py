from autobahn.twisted.websocket import WebSocketServerProtocol
from autobahn.twisted.websocket import WebSocketServerFactory, \
	WebSocketServerProtocol
from core import app
from collections import deque
import json
from twisted.python import log
from twisted.internet import reactor
from autobahn.twisted.resource import WebSocketResource, WSGIRootResource



class KillboardProtocol(WebSocketServerProtocol):
	def onConnect(self, request):
		self.factory.clients.append(self)
		reactor.callLater(1, self._sendBuffer)

	def _sendBuffer(self):
		self.sendMessage(json.dumps({'type':'status', 'msg': '* Playback start'}))
		for msg in list(self.factory.buffer):
			self.sendMessage(msg, False)
		self.sendMessage(json.dumps({'type':'status', 'msg': '* Playback complete'}))
	def onClose(self, wasClean, code, reason):
		self.factory.clients.remove(self)
	def onMessage(self, payload, isBinary):
		if isBinary == False:
			self.factory.broadcast(payload)
			self.factory.ps2api.sendMessage(payload)

class KillboardServerFactory(WebSocketServerFactory):
	counter = 0
	buffer = deque(maxlen=100)
	def broadcast(self, msg):
		#print "Broadcast #%s to %s clients (%s)" % (self.counter, len(self.clients), msg)
		self.counter += 1
		self.buffer.append(msg)
		for proto in self.clients:
			try:
				#print "send to %s %s" % (proto, msg)
				proto.sendMessage(msg, False)
			except:
				#print "exception"
				pass

wsFactory = KillboardServerFactory(u"ws://0.0.0.0:%s" % app.config['APP_PORT'],
debug=app.debug,
debugCodePaths=app.debug)

wsFactory.protocol = KillboardProtocol
wsFactory.clients = []
