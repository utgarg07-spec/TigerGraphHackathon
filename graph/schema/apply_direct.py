import json
from pyTigerGraph import TigerGraphConnection

with open('configs/local_server_config.json') as f:
    cfg = json.load(f)['db_config']

conn = TigerGraphConnection(
    host=cfg['hostname'],
    graphname=cfg['graphname'],
    username=cfg['username'],
    password=cfg['password'],
    restppPort=cfg.get('restppPort', '443'),
    gsPort=cfg.get('gsPort', '443')
)

with open('graph/schema/single_cmd.gsql', 'r') as f:
    lines = [l.strip() for l in f if l.strip() and not l.startswith('#')]

for stmt in lines:
    print(f"Executing: {stmt[:60]}...")
    res = conn.gsql(stmt)
    print("Result:", res)
