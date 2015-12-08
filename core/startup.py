from autobahn.twisted.websocket import connectWS, WebSocketClientFactory
import sys
from twisted.internet import ssl
from core import app
from core.listeners.kpm import KPMListener
from core.listeners.groupkill import GroupKillListener
from core.listeners.simpleevent import SimpleEventListener
from core.listeners.loginresolver import LoginResolverListener
from core.util.ps2client import PS2RealTimeClientProtocol
from core.util.websocket import KillboardServerFactory, KillboardProtocol

def startup():
	m = sys.modules[__name__]

	# set up the killboard websocket
	wsFactory = KillboardServerFactory(
		u"ws://0.0.0.0:%s" % app.config['APP_PORT'],
		debug=app.debug,
		debugCodePaths=app.debug
	)

	wsFactory.protocol = KillboardProtocol
	wsFactory.clients = []

	m.wsFactory = wsFactory

	# set up the real time event stream from the PS2 stats api
	factory = WebSocketClientFactory(u"wss://push.planetside2.com/streaming?environment=ps2&service-id=s:vanderpot", debug=True)
	# set up modules wanting to listen to the ps2 datastream
	# TODO: refactor websocket crap for live killfeed into a listener
	factory.listeners = {
		'infantrykpm': KPMListener(filter=lambda payload, character, attacker: payload['attacker_vehicle_id'] == '0'),
		'sundererkpm': KPMListener(filter=lambda payload, character, attacker: payload['attacker_vehicle_id'] == '2'),
		'tankkpm': KPMListener(filter=lambda payload, character, attacker: payload['attacker_vehicle_id'] in ('4', '5', '6')),
		'harasserkpm': KPMListener(filter=lambda payload, character, attacker: payload['attacker_vehicle_id'] == '12'),
		'lightningkpm': KPMListener(filter=lambda payload, character, attacker: payload['attacker_vehicle_id'] == '3'),
		'libkpm': KPMListener(filter=lambda payload, character, attacker: payload['attacker_vehicle_id'] == '10'),
		'esfkpm': KPMListener(filter=lambda payload, character, attacker: payload['attacker_vehicle_id'] in ('7','8','9')),
		'kpm': KPMListener(),
		'groupkill': GroupKillListener(),
		'simpleevent': SimpleEventListener(),
		'loginresolver': LoginResolverListener(),
	}
	factory.protocol = PS2RealTimeClientProtocol
	factory.receiver = wsFactory

	m.factory = factory

	contextFactory = ssl.ClientContextFactory()
	connectWS(factory, contextFactory)