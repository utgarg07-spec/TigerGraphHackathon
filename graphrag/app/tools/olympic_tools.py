# Copyright (c) 2024-2026 TigerGraph, Inc.
#
# This program may be redistributed and/or modified under the terms of the GNU
# Affero General Public License as published by the Free Software Foundation,
# either version 3 of the License, or (at your option) any later version.

"""Deterministic Olympic graph tools for the agentic engine.

Provides four deterministic, non-LLM tools operating directly against the
TigerGraph Olympic Event graph created in Phase 4:
1. graphrag__lookup: Find Event by title and return nations field.
2. graphrag__aggregate: Count events for sport+games where competitors > threshold.
3. graphrag__superlative: Return full title of Event with max competitors for sport+games.
4. graphrag__temporal_resolve: Resolve prior/next edition gold winner using prev_year/next_year graph links or sequence fallback.
"""

from __future__ import annotations

import difflib
import logging
import re
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# Fallback sequence cycles for Summer and Winter Olympics
SUMMER_YEARS = [
    2024, 2020, 2016, 2012, 2008, 2004, 2000, 1996, 1992, 1988, 1984, 1980,
    1976, 1972, 1968, 1964, 1960, 1956, 1952, 1948, 1936, 1932, 1928, 1924,
    1920, 1912, 1908, 1904, 1900, 1896
]

WINTER_YEARS = [
    2022, 2018, 2014, 2010, 2006, 2002, 1998, 1994, 1992, 1988, 1984, 1980,
    1976, 1972, 1968, 1964, 1960, 1956, 1952, 1948, 1936, 1932, 1928, 1924
]

KNOWN_SPORTS = [
    "short-track speed skating", "speed skating", "cross-country skiing", "nordic combined",
    "alpine skiing", "figure skating", "freestyle skiing", "biathlon", "bobsleigh", "luge",
    "skeleton", "snowboarding", "athletics", "swimming", "taekwondo", "wrestling", "fencing",
    "judo", "boxing", "cycling", "sailing", "rowing", "canoeing", "shooting", "gymnastics",
    "weightlifting", "archery", "badminton", "equestrian", "modern pentathlon", "table tennis",
    "tennis", "triathlon"
]


def _ok(summary: str, context: Any, citations: Optional[list] = None) -> dict:
    return {"ok": True, "summary": summary, "context": context, "citations": citations or []}


def _empty(summary: str) -> dict:
    return {"ok": False, "summary": summary, "context": None, "citations": []}


def _get_all_events(conn: Any) -> List[dict]:
    """Retrieve all Event vertices from TigerGraph.
    
    Uses pyTigerGraph connection getVertices or cached result.
    """
    if hasattr(conn, "_olympic_events_cache") and getattr(conn, "_olympic_events_cache"):
        return getattr(conn, "_olympic_events_cache")

    if hasattr(conn, "getVertices"):
        raw = conn.getVertices("Event", limit=3000)
        events = []
        for r in raw:
            attr = dict(r.get("attributes", {}))
            attr["v_id"] = r.get("v_id", attr.get("id", ""))
            events.append(attr)
        if hasattr(conn, "__dict__"):
            setattr(conn, "_olympic_events_cache", events)
        return events
    return []


# --------------------------------------------------------------------------
# 1. graphrag__lookup
# --------------------------------------------------------------------------

def graphrag__lookup(ctx: Any, event_title: str) -> dict:
    """Find Event by title and return its nations field.
    
    Deterministic matching: exact match first, dash/case normalized match second,
    fuzzy match fallback third.
    """
    if not event_title or not isinstance(event_title, str):
        return _empty("Invalid event_title argument")
        
    events = _get_all_events(ctx.conn if hasattr(ctx, "conn") else ctx)
    if not events:
        return _empty("No events available in graph")

    target = event_title.strip()
    target_norm = target.replace('–', '-').replace('—', '-').lower()

    matched = None
    # 1. Exact match on title or v_id
    for ev in events:
        if ev.get("title") == target or ev.get("v_id") == target:
            matched = ev
            break

    # 2. Normalized dash/case exact match
    if not matched:
        for ev in events:
            t = ev.get("title", "").replace('–', '-').replace('—', '-').lower()
            if t == target_norm:
                matched = ev
                break

    # 3. Deterministic fuzzy match
    if not matched:
        title_map = {}
        for ev in events:
            title_map.setdefault(ev.get("title", ""), ev)
            
        titles_sorted = sorted(title_map.keys())
        close = difflib.get_close_matches(target, titles_sorted, n=1, cutoff=0.6)
        if close:
            matched = title_map[close[0]]

    if not matched:
        return _empty(f"No event found matching '{event_title}'")

    nations = matched.get("nations", 0)
    event_id = matched.get("v_id", matched.get("id", ""))
    full_title = matched.get("title", target)

    return _ok(
        summary=str(nations),
        context={
            "event_title": full_title,
            "nations": str(nations),
            "event_id": event_id
        },
        citations=[{"id": f"Event/{event_id}"}]
    )


# --------------------------------------------------------------------------
# 2. graphrag__aggregate
# --------------------------------------------------------------------------

def graphrag__aggregate(ctx: Any, sport: str, games: str, threshold: int) -> dict:
    """Filter Event vertices by sport + games, count events where competitors > threshold.
    
    Returns count as string.
    """
    if not sport or not games:
        return _empty("Invalid sport or games argument")
        
    events = _get_all_events(ctx.conn if hasattr(ctx, "conn") else ctx)
    if not events:
        return _empty("No events available in graph")

    sport_l = sport.strip().lower()
    games_l = games.strip().lower()

    # Verify if sport + games exist in graph
    matching_sport_games = [
        ev for ev in events
        if (sport_l in ev.get("sport_name", "").lower() or ev.get("sport_name", "").lower() in sport_l)
        and (games_l in ev.get("games_name", "").lower() or ev.get("games_name", "").lower() in games_l or games_l in ev.get("title", "").lower())
    ]

    if not matching_sport_games:
        return _empty(f"No events found matching sport '{sport}' and games '{games}'")

    above_threshold = [
        ev for ev in matching_sport_games
        if ev.get("competitors", 0) > threshold
    ]

    count = len(above_threshold)
    citations = [{"id": f"Event/{ev.get('v_id', '')}"} for ev in above_threshold if ev.get('v_id')]

    return _ok(
        summary=str(count),
        context={
            "count": str(count),
            "sport": sport,
            "games": games,
            "threshold": threshold,
            "matched_events": [ev.get("title", "") for ev in above_threshold]
        },
        citations=citations
    )


# --------------------------------------------------------------------------
# 3. graphrag__superlative
# --------------------------------------------------------------------------

def graphrag__superlative(ctx: Any, sport: str, games: str) -> dict:
    """Filter Event vertices by sport + games and return full title of Event with max competitors."""
    if not sport or not games:
        return _empty("Invalid sport or games argument")
        
    events = _get_all_events(ctx.conn if hasattr(ctx, "conn") else ctx)
    if not events:
        return _empty("No events available in graph")

    sport_l = sport.strip().lower()
    games_l = games.strip().lower()

    matching = [
        ev for ev in events
        if (sport_l in ev.get("sport_name", "").lower() or ev.get("sport_name", "").lower() in sport_l)
        and (games_l in ev.get("games_name", "").lower() or ev.get("games_name", "").lower() in games_l or games_l in ev.get("title", "").lower())
    ]

    if not matching:
        return _empty(f"No events found matching sport '{sport}' and games '{games}'")

    # Sort deterministically by (competitors, title)
    matching.sort(key=lambda x: (x.get("competitors", 0), x.get("title", "")), reverse=True)
    best = matching[0]

    full_title = best.get("title", "")
    event_id = best.get("v_id", best.get("id", ""))

    return _ok(
        summary=full_title,
        context={
            "title": full_title,
            "sport": sport,
            "games": games,
            "competitors": best.get("competitors", 0),
            "event_id": event_id
        },
        citations=[{"id": f"Event/{event_id}"}]
    )


# --------------------------------------------------------------------------
# 4. graphrag__temporal_resolve
# --------------------------------------------------------------------------

def _score_event_match(candidate: dict, query_str: str) -> int:
    c_title = candidate.get("title", "").lower()
    c_event = candidate.get("event_name", "").lower()
    c_sport = candidate.get("sport_name", "").lower()
    q_norm = query_str.lower()

    # 1. Sport filter
    req_sport = None
    for s in KNOWN_SPORTS:
        if s in q_norm:
            req_sport = s
            break

    if req_sport:
        if req_sport == "speed skating" and "short" in c_sport:
            return -1000
        if req_sport not in c_sport and req_sport not in c_title:
            return -1000

    # 2. Gender filter
    if "women's" in q_norm or "women" in q_norm:
        if "women's" not in c_event and "women" not in c_event and "women's" not in c_title:
            return -1000
    elif "men's" in q_norm or "men" in q_norm:
        if "women's" in c_event or "women" in c_event or "women's" in c_title:
            return -1000

    score = 100
    tokens = re.findall(r'\b\w+\b', q_norm)
    stop_words = {"event", "at", "the", "olympics", "held", "immediately", "before", "after", "summer", "winter"}
    for token in tokens:
        if token in stop_words:
            continue
        if token in c_event:
            score += 20
        elif token in c_title:
            score += 10

    if c_event in q_norm or q_norm in c_event:
        score += 50

    return score


def _find_best_matching_event(candidates: List[dict], query_str: str) -> Optional[dict]:
    scored = []
    for c in candidates:
        s = _score_event_match(c, query_str)
        if s > 0:
            scored.append((s, c))
    if not scored:
        return None
    scored.sort(key=lambda x: (x[0], x[1].get("title", "")), reverse=True)
    return scored[0][1]


def graphrag__temporal_resolve(
    ctx: Any,
    event_name: str,
    season: str,
    reference_year: int,
    direction: str = "immediately before"
) -> dict:
    """Resolve prior/related edition gold winner using prev_year/next_year fields in graph first.
    
    Falls back to sequence math if prev/next field is missing.
    Returns gold field exactly as stored in graph.
    """
    if not event_name or not season or not reference_year:
        return _empty("Invalid arguments for temporal resolve")

    events = _get_all_events(ctx.conn if hasattr(ctx, "conn") else ctx)
    if not events:
        return _empty("No events available in graph")

    season_norm = season.strip().capitalize()
    dir_norm = direction.strip().lower()

    # Step 1: Search reference event in reference_year
    ref_candidates = [
        ev for ev in events
        if ev.get("year") == reference_year and ev.get("season") == season_norm
    ]
    ref_ev = _find_best_matching_event(ref_candidates, event_name)

    target_year = None
    used_prev_graph = False

    # Check graph prev_year / next_year link first
    if ref_ev:
        if "before" in dir_norm or "prior" in dir_norm:
            py = ref_ev.get("prev_year")
            if py is not None and py == 0:
                return _empty(f"No prior edition exists in graph for '{event_name}' ({reference_year})")
            elif py and py > 0:
                target_year = py
                used_prev_graph = True
        elif "after" in dir_norm or "next" in dir_norm:
            ny = ref_ev.get("next_year")
            if ny is not None and ny == 0:
                return _empty(f"No next edition exists in graph for '{event_name}' ({reference_year})")
            elif ny and ny > 0:
                target_year = ny
                used_prev_graph = True

    # Fallback to Summer/Winter sequence math if missing
    if not target_year:
        seq = SUMMER_YEARS if season_norm == "Summer" else WINTER_YEARS
        if "before" in dir_norm or "prior" in dir_norm:
            priors = [y for y in seq if y < reference_year]
            target_year = priors[0] if priors else None
        else:
            nexts = [y for y in seq if y > reference_year]
            target_year = nexts[-1] if nexts else None

    if not target_year:
        return _empty(f"Could not resolve prior edition year for '{event_name}' ({reference_year})")

    # Step 2: Search target event in target_year
    target_candidates = [
        ev for ev in events
        if ev.get("year") == target_year and ev.get("season") == season_norm
    ]

    target_ev = None
    if ref_ev:
        target_ev = _find_best_matching_event(target_candidates, ref_ev.get("event_name", ""))
    if not target_ev:
        target_ev = _find_best_matching_event(target_candidates, event_name)

    if not target_ev:
        return _empty(f"Target event for '{event_name}' in edition {target_year} not found in graph")

    raw_gold = target_ev.get("gold", "")
    event_id = target_ev.get("v_id", target_ev.get("id", ""))
    full_title = target_ev.get("title", "")

    return _ok(
        summary=raw_gold,
        context={
            "gold": raw_gold,
            "event_title": full_title,
            "event_id": event_id,
            "year": target_year,
            "used_prev_graph": used_prev_graph
        },
        citations=[{"id": f"Event/{event_id}"}]
    )
