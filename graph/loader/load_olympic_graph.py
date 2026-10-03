import json
import time
from pathlib import Path
from pyTigerGraph import TigerGraphConnection

def safe_int(val, default=0):
    if val is None:
        return default
    try:
        return int(val)
    except (ValueError, TypeError):
        return default

def safe_str(val, default=""):
    if val is None:
        return default
    return str(val)

def load_olympic_graph(
    config_path: str = "configs/local_server_config.json",
    events_path: str = "data/processed/events.jsonl",
):
    base_dir = Path(__file__).resolve().parent.parent.parent
    cfg_file = base_dir / config_path
    if not cfg_file.exists():
        cfg_file = Path(config_path)

    print(f"Loading configuration from {cfg_file}...")
    with open(cfg_file, "r", encoding="utf-8") as f:
        cfg = json.load(f)["db_config"]

    conn = TigerGraphConnection(
        host=cfg["hostname"],
        graphname=cfg["graphname"],
        username=cfg["username"],
        password=cfg["password"],
        restppPort=cfg.get("restppPort", "443"),
        gsPort=cfg.get("gsPort", "443"),
    )

    ev_file = base_dir / events_path
    if not ev_file.exists():
        ev_file = Path(events_path)
    if not ev_file.exists():
        raise FileNotFoundError(f"{events_path} not found.")

    records = []
    with open(ev_file, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                records.append(json.loads(line))

    print(f"Loaded {len(records)} event records from {ev_file}.")

    batch = {
        "vertices": {
            "Event": {},
            "Sport": {},
            "Games": {},
            "Venue": {},
            "NOCCountry": {},
        },
        "edges": {
            "Document": {},
            "Event": {},
        },
    }

    event_map = batch["vertices"]["Event"]
    sport_map = batch["vertices"]["Sport"]
    games_map = batch["vertices"]["Games"]
    venue_map = batch["vertices"]["Venue"]
    noc_map = batch["vertices"]["NOCCountry"]

    doc_edges = batch["edges"]["Document"]
    event_edges = batch["edges"]["Event"]

    for rec in records:
        doc_id = safe_str(rec.get("doc_id"))
        if not doc_id:
            continue

        title = safe_str(rec.get("title"))
        event_name = safe_str(rec.get("event"))
        games_name = safe_str(rec.get("games"))
        sport_name = safe_str(rec.get("sport"))
        venue_name = safe_str(rec.get("venue"))

        year = safe_int(rec.get("prev"), 0)
        season = ""
        if games_name:
            parts = games_name.split()
            if len(parts) >= 2 and parts[0].isdigit():
                year = safe_int(parts[0], 0)
                season = safe_str(parts[1])

        date_raw = safe_str(rec.get("date_raw"))
        competitors = safe_int(rec.get("competitors"), 0)
        nations = safe_int(rec.get("nations"), 0)

        gold = safe_str(rec.get("gold"))
        gold_noc = safe_str(rec.get("goldNOC"))
        silver = safe_str(rec.get("silver"))
        silver_noc = safe_str(rec.get("silverNOC"))
        bronze = safe_str(rec.get("bronze"))
        bronze_noc = safe_str(rec.get("bronzeNOC"))

        win_value = safe_str(rec.get("win_value"))
        prev_year = safe_int(rec.get("prev"), 0)
        next_year = safe_int(rec.get("next"), 0)

        # Event Vertex
        event_map[doc_id] = {
            "title": {"value": title},
            "event_name": {"value": event_name},
            "games_name": {"value": games_name},
            "sport_name": {"value": sport_name},
            "venue_name": {"value": venue_name},
            "year": {"value": year},
            "season": {"value": season},
            "date_raw": {"value": date_raw},
            "competitors": {"value": competitors},
            "nations": {"value": nations},
            "gold": {"value": gold},
            "gold_noc": {"value": gold_noc},
            "silver": {"value": silver},
            "silver_noc": {"value": silver_noc},
            "bronze": {"value": bronze},
            "bronze_noc": {"value": bronze_noc},
            "win_value": {"value": win_value},
            "prev_year": {"value": prev_year},
            "next_year": {"value": next_year},
        }

        # Sport Vertex
        if sport_name:
            sport_map[sport_name] = {"name": {"value": sport_name}}

        # Games Vertex
        if games_name:
            games_map[games_name] = {
                "year": {"value": year},
                "season": {"value": season},
            }

        # Venue Vertex
        if venue_name:
            venue_map[venue_name] = {"name": {"value": venue_name}}

        # Country Vertices
        for noc in [gold_noc, silver_noc, bronze_noc]:
            if noc:
                noc_map[noc] = {"noc_code": {"value": noc}}

        # Edges from Document to Event
        if doc_id not in doc_edges:
            doc_edges[doc_id] = {"DOCUMENT_HAS_EVENT": {"Event": {}}}
        doc_edges[doc_id]["DOCUMENT_HAS_EVENT"]["Event"][doc_id] = {}

        # Edges from Event to Sport, Games, Venue, Country
        if doc_id not in event_edges:
            event_edges[doc_id] = {}

        if sport_name:
            if "BELONGS_TO_SPORT" not in event_edges[doc_id]:
                event_edges[doc_id]["BELONGS_TO_SPORT"] = {"Sport": {}}
            event_edges[doc_id]["BELONGS_TO_SPORT"]["Sport"][sport_name] = {}

        if games_name:
            if "HELD_IN_GAMES" not in event_edges[doc_id]:
                event_edges[doc_id]["HELD_IN_GAMES"] = {"Games": {}}
            event_edges[doc_id]["HELD_IN_GAMES"]["Games"][games_name] = {}

        if venue_name:
            if "HELD_AT_VENUE" not in event_edges[doc_id]:
                event_edges[doc_id]["HELD_AT_VENUE"] = {"Venue": {}}
            event_edges[doc_id]["HELD_AT_VENUE"]["Venue"][venue_name] = {}

        if gold_noc:
            if "WON_BY_GOLD" not in event_edges[doc_id]:
                event_edges[doc_id]["WON_BY_GOLD"] = {"NOCCountry": {}}
            event_edges[doc_id]["WON_BY_GOLD"]["NOCCountry"][gold_noc] = {}

        if silver_noc:
            if "WON_BY_SILVER" not in event_edges[doc_id]:
                event_edges[doc_id]["WON_BY_SILVER"] = {"NOCCountry": {}}
            event_edges[doc_id]["WON_BY_SILVER"]["NOCCountry"][silver_noc] = {}

        if bronze_noc:
            if "WON_BY_BRONZE" not in event_edges[doc_id]:
                event_edges[doc_id]["WON_BY_BRONZE"] = {"NOCCountry": {}}
            event_edges[doc_id]["WON_BY_BRONZE"]["NOCCountry"][bronze_noc] = {}

    print("Upserting deterministic Olympic knowledge graph into TigerGraph...")
    start_time = time.time()
    res = conn.upsertData(json.dumps(batch))
    elapsed = round(time.time() - start_time, 2)
    print(f"Deterministic load complete in {elapsed}s. Response: {res}")


if __name__ == "__main__":
    load_olympic_graph()
