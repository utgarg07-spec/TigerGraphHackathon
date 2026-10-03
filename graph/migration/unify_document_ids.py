import sys
import os
import json
import argparse
from pyTigerGraph import TigerGraphConnection

CONFIG_PATH = "configs/local_server_config.json"
BACKUP_PATH = "graph/migration/migration_backup.json"
TEST_TARGET_IDS = ["Q1005784", "Q1043342", "Q1043347", "Q1043354", "Q1043361"]

def get_tg_connection():
    with open(CONFIG_PATH, "r") as f:
        cfg = json.load(f)

    db_cfg = cfg["db_config"]
    conn = TigerGraphConnection(
        host=db_cfg["hostname"],
        graphname=db_cfg["graphname"],
        username=db_cfg.get("username", "tigergraph"),
        password=db_cfg.get("password", "tigergraph"),
        restppPort=db_cfg.get("restppPort", 9000),
        gsPort=db_cfg.get("gsPort", 14240)
    )
    return conn

def run_verify(conn):
    print("==================================================")
    print("STAGE 3 — POST-MIGRATION VERIFICATION")
    print("==================================================")

    docs = conn.getVertices("Document", limit=10000)
    u_docs_after = [d["v_id"] for d in docs if d["v_id"].startswith("Q")]
    l_docs_after = [d["v_id"] for d in docs if d["v_id"].startswith("q")]

    content_total_after = conn.getVertexCount("Content")
    chunk_total_after = conn.getVertexCount("DocumentChunk")
    event_total_after = conn.getVertexCount("Event")

    print(f"1. Total Documents: {len(docs)} (Expected: 2162)")
    print(f"2. Uppercase Q... Documents: {len(u_docs_after)} (Expected: 2162)")
    print(f"3. Lowercase q... Documents: {len(l_docs_after)} (Expected: 0)")
    print(f"4. Total Content vertices: {content_total_after} (Expected: 2391)")
    print(f"5. Total DocumentChunk vertices: {chunk_total_after} (Expected: 228 or 229)")
    print(f"6. Total Event vertices: {event_total_after} (Expected: 2162)")

    assert len(docs) == 2162, f"Post-check failed: total docs {len(docs)}"
    assert len(u_docs_after) == 2162, f"Post-check failed: uppercase docs {len(u_docs_after)}"
    assert len(l_docs_after) == 0, f"Post-check failed: lowercase docs {len(l_docs_after)}"
    assert content_total_after == 2391, f"Post-check failed: content total {content_total_after}"
    assert event_total_after == 2162, f"Post-check failed: event total {event_total_after}"

    # Verify 5 Step C test targets
    print("\nVerifying 5 Step C target documents post-migration...")
    for target in TEST_TARGET_IDS:
        target_u = target.upper()
        target_l = target.lower()

        u_check = conn.getVerticesById("Document", target_u)
        
        l_check_count = 0
        try:
            l_check = conn.getVerticesById("Document", target_l)
            l_check_count = len(l_check)
        except Exception:
            l_check_count = 0

        assert len(u_check) == 1, f"Expected 1 vertex for {target_u}, got {len(u_check)}"
        assert l_check_count == 0, f"Expected 0 vertices for {target_l}, got {l_check_count}"

        # Check content edge
        edges = conn.getEdges("Document", target_u)
        has_c = any(e["e_type"] == "HAS_CONTENT" for e in edges)
        assert has_c, f"Target {target_u} has no HAS_CONTENT edge post-migration"
        print(f"  Target {target}: Uniquely resolves to {target_u} | HAS_CONTENT=True | Lowercase doc=Deleted (0)")

    # Representative check: Q1005784
    rep_edges = conn.getEdges("Document", "Q1005784")
    rep_has_c = any(e["e_type"] == "HAS_CONTENT" for e in rep_edges)
    rep_has_ev = any(e["e_type"] == "DOCUMENT_HAS_EVENT" for e in rep_edges)
    assert rep_has_c and rep_has_ev, f"Representative Q1005784 check failed: HAS_CONTENT={rep_has_c}, HAS_EVENT={rep_has_ev}"
    print(f"\nRepresentative Document Q1005784 verification PASSED (HAS_CONTENT={rep_has_c}, DOCUMENT_HAS_EVENT={rep_has_ev}).")

    print("\n==================================================")
    print("ALL POST-MIGRATION VERIFICATIONS PASSED SUCCESSFULLY!")
    print("==================================================")

if __name__ == "__main__":
    conn = get_tg_connection()
    run_verify(conn)
