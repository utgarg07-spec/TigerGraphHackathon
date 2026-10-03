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

with open('graph/schema/olympic_schema.gsql', 'r', encoding='utf-8') as f:
    gsql_text = f.read()

print("Applying schema change job...")
res = conn.gsql(gsql_text)
print("Schema Change Result:")
print(res)
