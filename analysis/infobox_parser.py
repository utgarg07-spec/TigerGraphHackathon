"""
Deterministic Infobox Parser for Olympics Corpus.

Pure Python/regex infobox parser with no LLM calls.
Extracts structured fields from Wikipedia infobox headers in data/corpus.jsonl.
Preserves raw medal strings without modifying concatenated team names.
"""

import re
from typing import Dict, Any, Optional, Tuple


def parse_infobox_raw(text: str) -> Tuple[Optional[str], Dict[str, str]]:
    """
    Extracts the leading infobox type and key-value pair dictionary from document text.
    
    Args:
        text: Raw text of document.
        
    Returns:
        Tuple of (infobox_type, raw_key_value_dict)
    """
    if not text:
        return None, {}

    lines = text.splitlines()
    infobox_type = None
    in_infobox = False
    raw_fields: Dict[str, str] = {}

    for line in lines:
        line_str = line.strip()
        
        # Detect infobox header, e.g., [Infobox Olympic event] or {{Infobox film
        if not in_infobox:
            ib_match = re.match(r'^(?:\[|\{\{)Infobox\s+([^\]\}\n]+)', line_str, re.IGNORECASE)
            if ib_match:
                infobox_type = ib_match.group(1).strip()
                in_infobox = True
                continue
            # Also check if infobox appears within first 3 lines
            ib_match_any = re.search(r'(?:\[|\{\{)Infobox\s+([^\]\}\n]+)', line_str, re.IGNORECASE)
            if ib_match_any:
                infobox_type = ib_match_any.group(1).strip()
                in_infobox = True
                continue
        else:
            # End of infobox block when empty line or line that is not indented key-value
            if line_str == '':
                break
            if not line.startswith('  ') and not (':' in line or '=' in line):
                break
            
            # Key-value line parsing
            if ':' in line or '=' in line:
                parts = re.split(r'[:=]', line, maxsplit=1)
                if len(parts) == 2:
                    k = parts[0].strip()
                    v = parts[1].strip()
                    if k:
                        raw_fields[k] = v

    return infobox_type, raw_fields


def _parse_int_field(val: Optional[str]) -> Optional[int]:
    """Parses integer from string field if parseable, otherwise returns None."""
    if val is None or val == '':
        return None
    val_clean = val.strip()
    if val_clean.isdigit():
        return int(val_clean)
    digits = re.findall(r'\d+', val_clean)
    if digits:
        try:
            return int(digits[0])
        except ValueError:
            return None
    return None


def extract_sport_from_title(title: str) -> Optional[str]:
    """
    Deterministically recovers sport name from document title if present.
    Example: "Canoeing at the 2012 Summer Olympics – Men's K-2 1000 metres" -> "Canoeing"
    """
    if not title:
        return None
    
    match = re.match(r'^(.+?)\s+at the\s+\d{4}\s+(?:Summer|Winter)\s+Olympics', title, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    
    match2 = re.match(r'^(.+?)\s+at the\s+\d{4}', title, re.IGNORECASE)
    if match2:
        return match2.group(1).strip()
        
    return None


def parse_corpus_document(doc: Dict[str, Any]) -> Dict[str, Any]:
    """
    Parses a single document from data/corpus.jsonl into structured representation.
    
    Args:
        doc: JSON dict representing document record.
        
    Returns:
        Parsed structured record.
    """
    doc_id = doc.get('doc_id')
    title = doc.get('title', '')
    text = doc.get('text', '')

    ib_type, fields = parse_infobox_raw(text)
    
    is_olympic = bool(ib_type and ib_type.lower() == 'olympic event')

    sport = extract_sport_from_title(title) if is_olympic else None

    # Venue logic: venue or venues fallback
    venue = fields.get('venue') or fields.get('venues')
    if venue == '':
        venue = None

    # Date logic: date or dates fallback
    date_raw = fields.get('date') or fields.get('dates')
    if date_raw == '':
        date_raw = None

    # Medals must be stored strictly as RAW STRINGS exactly as they appear
    gold = fields.get('gold') if fields.get('gold') != '' else None
    goldNOC = fields.get('goldNOC') if fields.get('goldNOC') != '' else None
    silver = fields.get('silver') if fields.get('silver') != '' else None
    silverNOC = fields.get('silverNOC') if fields.get('silverNOC') != '' else None
    bronze = fields.get('bronze') if fields.get('bronze') != '' else None
    bronzeNOC = fields.get('bronzeNOC') if fields.get('bronzeNOC') != '' else None

    parsed_record = {
        'doc_id': doc_id,
        'title': title,
        'is_olympic_event': is_olympic,
        'infobox_type': ib_type,
        'event': fields.get('event') if fields.get('event') != '' else None,
        'games': fields.get('games') if fields.get('games') != '' else None,
        'sport': sport,
        'venue': venue,
        'date_raw': date_raw,
        'competitors': _parse_int_field(fields.get('competitors')),
        'nations': _parse_int_field(fields.get('nations')),
        'gold': gold,
        'goldNOC': goldNOC,
        'silver': silver,
        'silverNOC': silverNOC,
        'bronze': bronze,
        'bronzeNOC': bronzeNOC,
        'win_value': fields.get('win_value') if fields.get('win_value') != '' else None,
        'prev': _parse_int_field(fields.get('prev')),
        'next': _parse_int_field(fields.get('next')),
        'raw_fields': fields
    }

    return parsed_record
