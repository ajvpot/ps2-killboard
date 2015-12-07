from autobahn.twisted.websocket import connectWS, WebSocketClientFactory
from twisted.internet import ssl
from core import app
from core.util.ps2client import PS2RealTimeClientProtocol
from core.util.websocket import KillboardServerFactory, KillboardProtocol

def startup():
	# set up the killboard websocket
	wsFactory = KillboardServerFactory(
		u"ws://0.0.0.0:%s" % app.config['APP_PORT'],
		debug=app.debug,
		debugCodePaths=app.debug
	)

	wsFactory.protocol = KillboardProtocol
	wsFactory.clients = []

	# set up the real time event stream from the PS2 stats api
	factory = WebSocketClientFactory(u"wss://push.planetside2.com/streaming?environment=ps2&service-id=s:vanderpot", debug=True)
	factory.protocol = PS2RealTimeClientProtocol
	factory.receiver = wsFactory

	contextFactory = ssl.ClientContextFactory()
	connectWS(factory, contextFactory)