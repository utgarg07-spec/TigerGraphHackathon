# TigerGraph Model Context Protocol (MCP) Interoperability

**Status**: **INTEGRATED & VERIFIED**  
**Package**: `tigergraph-mcp` (v1.0.3)  
**Security Model**: Strict Read-Only Sandbox (No Destructive GSQL/Schema Operations)  
**Primary Integration Layer**: [`graphrag/app/tools/tg_mcp_tools.py`](file:///d:/Hackathons/TigerGraph/graphrag/app/tools/tg_mcp_tools.py)  
**Specialist Capability Backend**: `TigerGraphMCPSpecialist` in [`graphrag/app/agent/specialists.py`](file:///d:/Hackathons/TigerGraph/graphrag/app/agent/specialists.py)  

---

## 1. Executive Summary & Design Principles

The official [TigerGraph Model Context Protocol (MCP)](https://github.com/tigergraph/tigergraph-mcp) server has been integrated as an **additive, interoperable capability layer**.

### Core Tenets:
1. **Additive Only**: Does NOT replace deterministic Olympic tools, vector/hybrid retrievers, or existing installed GSQL queries.
2. **Strict Read-Only Sandbox**: Only read-only operations (`tg_run_query`, `tg_get_neighbors`, `tg_run_installed_query`) are exposed. All destructive tools (`drop`, `delete`, `insert`, `update`, `upsert`, schema modifications) are blocked.
3. **Per-User Context Injection**: Uses thread-safe `contextvars` to dynamically pass per-request TigerGraph credentials without sharing connection state across concurrent users.
4. **Specialist Agent Integration**: Accessible as an optional specialist backend (`TigerGraphMCPSpecialist`) within the `SpecialistOrchestrator`.

---

## 2. Allowed MCP Tool Set

| MCP Tool Name | Underlying MCP Function | Capability | Destructive? |
| :--- | :--- | :--- | :---: |
| **`tg_run_query`** | `tigergraph_mcp.tools.query_tools.run_query` | Executes read-only interpreted GSQL queries (e.g. ad-hoc entity exploration, count queries). | **No (Read-Only)** |
| **`tg_get_neighbors`** | `tigergraph_mcp.tools.query_tools.get_neighbors` | Expands neighbors of a vertex given type, ID, and edge type without writing GSQL. | **No (Read-Only)** |
| **`tg_run_installed_query`** | `tigergraph_mcp.tools.query_tools.run_installed_query` | Invokes pre-installed GSQL queries by name with structured parameters. | **No (Read-Only)** |

---

## 3. Specialist Agent Layer Integration

The MCP layer is exposed via `TigerGraphMCPSpecialist` in [`graphrag/app/agent/specialists.py`](file:///d:/Hackathons/TigerGraph/graphrag/app/agent/specialists.py):

```python
class TigerGraphMCPSpecialist(SpecialistAgent):
    name: str = "TigerGraphMCPSpecialist"

    def execute(self, action: str, params: Dict[str, Any], ctx: Any) -> SpecialistOutput:
        # Dispatches to read-only tg_run_query or tg_get_neighbors
        # Emits structured SpecialistTelemetry with latency and evidence
```

### Telemetry Output:
```json
{
  "specialist_name": "TigerGraphMCPSpecialist",
  "action": "run_query",
  "input_summary": "query_text='INTERPRET QUERY () FOR GRAPH Olympics { S = {Sport.*}; PRINT S.size() AS total_sports; }'",
  "tool_used": "tg_run_query",
  "result_summary": "tg_run_query: ok",
  "latency_ms": 1007.1,
  "tokens": null,
  "evidence_added": {
    "mcp_context": {
      "function_call": "tg_run_query",
      "result": { "success": true, "data": { "result": [{ "total_sports": 41 }] } }
    }
  },
  "recommendation": "continue"
}
```

---

## 4. Verification & Audit Gate Results

**Verification Script**: [`scratch/test_tigergraph_mcp.py`](file:///d:/Hackathons/TigerGraph/scratch/test_tigergraph_mcp.py)  
**Execution Command**: `docker exec graphrag python scratch/test_tigergraph_mcp.py`

| Verification Step | Target Operation | Status | Latency |
| :--- | :--- | :---: | :---: |
| **1. Package Import** | `tigergraph_mcp` (v1.0.3) | **PASS** | < 5 ms |
| **2. Authentication** | Read-only connection to `Olympics` graph | **PASS** | ~120 ms |
| **3. Sandbox Security** | Assert 0 destructive tools exposed | **PASS** | < 1 ms |
| **4. Interpreted Read Query** | Count `Event` vertices (`2,162` total events) | **PASS** | 1,139 ms |
| **5. Olympic Event Lookup** | Retrieve nations for 2016 Sailing RS:X (`26`) | **PASS** | 1,001 ms |
| **6. Neighbor Expansion** | Expand `Event` -> `Sport` via `BELONGS_TO_SPORT` | **PASS** | 1,140 ms |
| **7. Specialist Integration** | Dispatch `TigerGraphMCPSpecialist` in orchestrator | **PASS** | 1,007 ms |

---

## 5. Non-Regression Confirmation

- **Phase 6 Deterministic Suite**: **`78 / 78 PASS (100.0%)`** in `graphrag/app/tools/test_olympic_tools.py`.
- **Phase 7 Orchestration Smoke Test**: **`10 / 10 PASS`** in `graphrag/tests/test_phase7_orchestrator_integration.py`.
- **Primary Benchmark Path**: Authoritative evaluation remains on deterministic GSQL tools; MCP provides an interoperable read interface for external LLMs and MCP clients.
