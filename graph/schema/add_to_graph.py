import json
from pyTigerGraph import TigerGraphConnection

with open('configs/local_server_config.json') as f:
    cfg = json.load(f)['db_config']

conn = TigerGraphConnection(
    host=cfg['hostname'],
    username=cfg['username'],
    password=cfg['password'],
    restppPort=cfg.get('restppPort', '443'),
    gsPort=cfg.get('gsPort', '443')
)

cmd = """
change job add_to_olympics for graph Olympics {
    ADD VERTEX Event, Sport, Games, Venue, NOCCountry;
    ADD EDGE BELONGS_TO_SPORT, HELD_IN_GAMES, HELD_AT_VENUE, WON_BY_GOLD, WON_BY_SILVER, WON_BY_BRONZE, DOCUMENT_HAS_EVENT;
}
run job add_to_olympics
drop job add_to_olympics
"""

res = conn.gsql(cmd)
print("Result:")
print(res)
