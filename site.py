import sys

from autobahn.twisted.resource import WSGIRootResource
from twisted.internet import reactor
from twisted.python import log
from twisted.web.client import HTTPClientFactory
from twisted.web.resource import Resource
from twisted.web.server import Site
from twisted.web.wsgi import WSGIResource

from core import app
from core.websocket.killboard import killboardResource
from util.reverseProxiedMiddleware import ReverseProxied

# disable httpclientfactory noise
HTTPClientFactory.noisy = False


app.debug = True
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

	import core.startup
	core.startup.startup()

	##
	# create a Twisted Web WSGI resource for our Flask server
	##
	wsgiResource = WSGIResource(reactor, reactor.getThreadPool(), app)

	wsResource = Resource()
	wsResource.putChild('killboard', killboardResource)

	##
	# create a root resource serving everything via WSGI/Flask, but
	# the path "/ws" served by our WebSocket stuff
	##
	rootResource = WSGIRootResource(wsgiResource, {'ws': wsResource})
	site = Site(rootResource)
	reactor.listenTCP(app.config['APP_PORT'], site, interface="0.0.0.0")

	# import core.util.ps2client
	# import core.util.ps2cache

	reactor.run()
