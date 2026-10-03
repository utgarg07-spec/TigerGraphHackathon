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

stmt = """
INTERPRET SCHEMA CHANGE JOB add_to_olympics FOR GRAPH Olympics {
    ADD VERTEX Event, Sport, Games, Venue, NOCCountry;
    ADD EDGE BELONGS_TO_SPORT, HELD_IN_GAMES, HELD_AT_VENUE, WON_BY_GOLD, WON_BY_SILVER, WON_BY_BRONZE, DOCUMENT_HAS_EVENT;
}
"""

print("Executing INTERPRET SCHEMA CHANGE JOB...")
res = conn.gsql(stmt)
print("Result:", res)
