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

cmd = """USE GRAPH Olympics

SCHEMA CHANGE JOB add_olympic_schema FOR GRAPH Olympics {
    ADD VERTEX Event(PRIMARY_ID id STRING, title STRING, event_name STRING, games_name STRING, sport_name STRING, venue_name STRING, year INT, season STRING, date_raw STRING, competitors INT, nations INT, gold STRING, gold_noc STRING, silver STRING, silver_noc STRING, bronze STRING, bronze_noc STRING, win_value STRING, prev_year INT, next_year INT) WITH STATS="OUTDEGREE_BY_EDGETYPE", PRIMARY_ID_AS_ATTRIBUTE="true";
    ADD VERTEX Sport(PRIMARY_ID id STRING, name STRING) WITH STATS="OUTDEGREE_BY_EDGETYPE", PRIMARY_ID_AS_ATTRIBUTE="true";
    ADD VERTEX Games(PRIMARY_ID id STRING, year INT, season STRING) WITH STATS="OUTDEGREE_BY_EDGETYPE", PRIMARY_ID_AS_ATTRIBUTE="true";
    ADD VERTEX Venue(PRIMARY_ID id STRING, name STRING) WITH STATS="OUTDEGREE_BY_EDGETYPE", PRIMARY_ID_AS_ATTRIBUTE="true";
    ADD VERTEX Country(PRIMARY_ID id STRING, noc_code STRING) WITH STATS="OUTDEGREE_BY_EDGETYPE", PRIMARY_ID_AS_ATTRIBUTE="true";

    ADD DIRECTED EDGE BELONGS_TO_SPORT(FROM Event, TO Sport) WITH REVERSE_EDGE="reverse_BELONGS_TO_SPORT";
    ADD DIRECTED EDGE HELD_IN_GAMES(FROM Event, TO Games) WITH REVERSE_EDGE="reverse_HELD_IN_GAMES";
    ADD DIRECTED EDGE HELD_AT_VENUE(FROM Event, TO Venue) WITH REVERSE_EDGE="reverse_HELD_AT_VENUE";
    ADD DIRECTED EDGE WON_BY_GOLD(FROM Event, TO Country) WITH REVERSE_EDGE="reverse_WON_BY_GOLD";
    ADD DIRECTED EDGE WON_BY_SILVER(FROM Event, TO Country) WITH REVERSE_EDGE="reverse_WON_BY_SILVER";
    ADD DIRECTED EDGE WON_BY_BRONZE(FROM Event, TO Country) WITH REVERSE_EDGE="reverse_WON_BY_BRONZE";
    ADD DIRECTED EDGE DOCUMENT_HAS_EVENT(FROM Document, TO Event) WITH REVERSE_EDGE="reverse_DOCUMENT_HAS_EVENT";
}
RUN SCHEMA CHANGE JOB add_olympic_schema
DROP JOB add_olympic_schema
"""

print("Executing schema change job...")
res = conn.gsql(cmd)
print(res)
