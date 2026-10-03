import json
from pyTigerGraph import TigerGraphConnection

cfg = json.load(open('configs/local_server_config.json'))['db_config']
conn = TigerGraphConnection(
    host=cfg['hostname'],
    graphname=cfg['graphname'],
    username=cfg['username'],
    password=cfg['password'],
    restppPort=cfg['restppPort'],
    gsPort=cfg['gsPort']
)
conn.getToken()

# Test 1: getVertices with where clause
v1 = conn.getVertices("Event", where='sport_name="Biathlon"')
print(f"Biathlon count via where: {len(v1)}")

# Test 2: getVertices for all Event vertices
v_all = conn.getVertices("Event", limit=3000)
print(f"Total Event vertices: {len(v_all)}")
