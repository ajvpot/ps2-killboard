from core.websocket.killboard import transactions as killboardTransactions
class KillboardRouter(object):
	def broadcast(self, msg):
		for transaction in killboardTransactions:
			transaction.fromCensus(msg)