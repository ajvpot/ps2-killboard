from core.ps2data import cache

class LoginResolverListener(object):
	def onMessage(self, payload):
		if(payload['event_name'] == "PlayerLogin"):
			cache.get('character', payload['character_id']) # Resolve character for webui