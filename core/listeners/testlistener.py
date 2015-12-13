from core.util.ps2message import fromCensus

class TestListener(object):
	def onMessage(self, payload):
		messageObject = fromCensus(payload)
		if messageObject is not None:
			print messageObject.pullData()