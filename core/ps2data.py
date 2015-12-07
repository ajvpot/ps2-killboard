# this module contains live instances of data classes:
from core import app
from core.util.ps2cache import CharacterResolver, PS2Cache

resolver = CharacterResolver(app.config['PS2_QUERY_INTERVAL'])
cache = PS2Cache(resolver)
cache.populate()