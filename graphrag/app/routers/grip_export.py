# Copyright (c) 2024-2026 TigerGraph, Inc.
#
# This program may be redistributed and/or modified under the terms of the GNU
# Affero General Public License as published by the Free Software Foundation,
# either version 3 of the License, or (at your option) any later version.

"""GRIP v0.5.0 Export / Interoperability Router.

This router provides an isolated, read-only HTTP export endpoint for converting
completed GraphRAGResponse payloads into GRIP v0.5.0 canonical envelopes.

Design Rules:
- Downstream transformation only: does not invoke LLMs, TigerGraph, or retrievers.
- Fully isolated: failures in export do not affect the main pipeline.
- Pure Pydantic request/response validation.
"""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from common.protocols.grip_adapter import (
    GRIPAdapter,
    GRIPCanonicalEnvelope,
)
from common.py_schemas.schemas import GraphRAGResponse

logger = logging.getLogger(__name__)

router = APIRouter(tags=["GRIP Interoperability"])


class GRIPExportRequest(BaseModel):
    """Request payload for exporting a completed GraphRAG response to GRIP."""
    response: GraphRAGResponse
    request_id: Optional[str] = Field(default=None, description="Optional caller request ID to preserve")
    latency_us: Optional[int] = Field(default=None, description="Optional execution latency in microseconds")
    llm_calls: Optional[int] = Field(default=None, description="Optional count of LLM calls made during execution")
    cost_usd: Optional[float] = Field(default=None, description="Optional monetary cost in USD")
    engine: str = Field(default="tigergraph", description="Graph database / engine name")


@router.post("/grip/export", response_model=GRIPCanonicalEnvelope, status_code=status.HTTP_200_OK)
def export_grip_envelope(request: GRIPExportRequest) -> GRIPCanonicalEnvelope:
    """Convert an existing, completed GraphRAGResponse into a canonical GRIP v0.5.0 envelope."""
    try:
        envelope = GRIPAdapter.from_graphrag_response(
            response=request.response,
            request_id=request.request_id,
            latency_us=request.latency_us,
            llm_calls=request.llm_calls,
            cost_usd=request.cost_usd,
            engine=request.engine,
        )
        return envelope
    except Exception as exc:
        logger.error(f"GRIP export transformation error: {exc}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Failed to transform GraphRAG response to GRIP envelope: {str(exc)}",
        )
