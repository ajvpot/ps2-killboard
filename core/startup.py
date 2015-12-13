import sys

from autobahn.twisted.websocket import connectWS, WebSocketClientFactory
from twisted.internet import ssl

from core.listeners.esfcounter import ESFCounterListener
from core.listeners.groupkill import GroupKillListener
from core.listeners.kpm import KPMListener
from core.listeners.loginresolver import LoginResolverListener
from core.util.ps2client import PS2RealTimeClientProtocol
from core.listeners.killboardlistener import KillboardListener
from core.listeners.testlistener import TestListener
from core.listeners.simpleevent import SimpleEventListener


def startup():
	m = sys.modules[__name__]

	# set up the real time event stream from the PS2 stats api
	factory = WebSocketClientFactory(u"wss://push.planetside2.com/streaming?environment=ps2&service-id=s:vanderpot", debug=True)
	# set up modules wanting to listen to the ps2 datastream
	factory.listeners = {
		'esfcounter': ESFCounterListener(),
		'tkkpm': KPMListener(filter=lambda payload, character, attacker: attacker['faction'] == character['faction'], filter_tks=False),
		'suicidekpm': KPMListener(filter=lambda payload, character, attacker: payload['attacker_character_id'] == payload['character_id'] or payload['attacker_character_id'] == 0, filter_tks=False, filter_suicides=False),
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
		'killboardrouter': KillboardListener(),
		'testlistener': TestListener(),
	}
	factory.protocol = PS2RealTimeClientProtocol

	m.factory = factory

	contextFactory = ssl.ClientContextFactory()
	connectWS(factory, contextFactory)
