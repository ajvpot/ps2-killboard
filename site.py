from twisted.web.wsgi import WSGIResource
from twisted.internet import reactor
from twisted.web.server import Site
from twisted.python import log
from core import app
from util.reverseProxiedMiddleware import ReverseProxied
import sys
from twisted.web.client import HTTPClientFactory
from autobahn.twisted.websocket import WebSocketServerFactory, \
	WebSocketServerProtocol
from autobahn.twisted.resource import WebSocketResource, WSGIRootResource
from core.util.websocket import wsFactory

# disable httpclientfactory noise
HTTPClientFactory.noisy = False


app.debug = False
app.testing = False

if __name__ == '__main__':
	# Wrap debug
	if app.debug:
		from werkzeug.debug import DebuggedApplication
		app.wsgi_app = DebuggedApplication(app.wsgi_app, True)
	# Wrap reverse proxy
	app.wsgi_app = ReverseProxied(app.wsgi_app)

	#app.run(port=7000, debug=True, host='0.0.0.0', threaded=True)

	log.startLogging(sys.stdout)
	log.msg('Starting app')

	##
	# create a Twisted Web resource for our WebSocket server
	##
	wsResource = WebSocketResource(wsFactory)

	##
	# create a Twisted Web WSGI resource for our Flask server
	##
	wsgiResource = WSGIResource(reactor, reactor.getThreadPool(), app)

	##
	# create a root resource serving everything via WSGI/Flask, but
	# the path "/ws" served by our WebSocket stuff
	##
	rootResource = WSGIRootResource(wsgiResource, {'ws': wsResource})
	site = Site(rootResource)
	reactor.listenTCP(app.config['APP_PORT'], site, interface="0.0.0.0")

	import core.util.ps2client
	import core.util.ps2cache

	reactor.run()
