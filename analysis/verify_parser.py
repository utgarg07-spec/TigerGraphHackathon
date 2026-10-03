"""
Parser Verification Script for Task 4.

Verifies:
1. 10 normal Olympic documents.
2. 5 Olympic documents containing missing/irregular fields.
3. 5 team-event documents with concatenated medal strings.
4. 5 non-Olympic distractor documents.
5. Explicit assertion that concatenated medal strings remain raw without modification.
"""

import json
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from analysis.infobox_parser import parse_corpus_document


def run_verification():
    corpus_path = Path("data/corpus.jsonl")
    if not corpus_path.exists():
        print(f"Error: {corpus_path} not found.")
        sys.exit(1)

    all_docs = []
    with open(corpus_path, "r", encoding="utf-8") as f:
        for line in f:
            all_docs.append(json.loads(line))

    print(f"Loaded {len(all_docs)} corpus documents.")

    normal_olympic = []
    irregular_olympic = []
    team_event_olympic = []
    non_olympic = []

    for doc in all_docs:
        parsed = parse_corpus_document(doc)
        if parsed["is_olympic_event"]:
            # Check concatenated medal string (e.g. Erik Lesser or multiple capitalized words without space/comma)
            gold = parsed.get("gold") or ""
            silver = parsed.get("silver") or ""
            bronze = parsed.get("bronze") or ""
            has_concatenated = any(
                ("Daniel" in name or "Schempp" in name or "Emanuel" in name or len(name) > 25)
                for name in [gold, silver, bronze]
            )
            
            # Check missing/irregular fields
            is_irregular = (
                parsed["competitors"] is None
                or parsed["nations"] is None
                or parsed["venue"] is None
                or parsed["prev"] is None
                or parsed["next"] is None
            )

            if has_concatenated and len(team_event_olympic) < 5:
                team_event_olympic.append((doc, parsed))
            elif is_irregular and len(irregular_olympic) < 5:
                irregular_olympic.append((doc, parsed))
            elif not is_irregular and len(normal_olympic) < 10:
                normal_olympic.append((doc, parsed))
        else:
            if len(non_olympic) < 5:
                non_olympic.append((doc, parsed))

    print("\n" + "=" * 60)
    print("VERIFICATION TEST 1: 10 Normal Olympic Documents")
    print("=" * 60)
    for i, (doc, parsed) in enumerate(normal_olympic, 1):
        print(f"[{i}] doc_id: {parsed['doc_id']} | title: {parsed['title']}")
        print(f"    event: {parsed['event']} | games: {parsed['games']} | sport: {parsed['sport']}")
        print(f"    venue: {parsed['venue']} | date_raw: {parsed['date_raw']}")
        print(f"    competitors: {parsed['competitors']} | nations: {parsed['nations']}")
        print(f"    gold: {parsed['gold']} ({parsed['goldNOC']})")
        print(f"    prev: {parsed['prev']} | next: {parsed['next']}\n")

    print("=" * 60)
    print("VERIFICATION TEST 2: 5 Olympic Documents with Missing/Irregular Fields")
    print("=" * 60)
    for i, (doc, parsed) in enumerate(irregular_olympic, 1):
        print(f"[{i}] doc_id: {parsed['doc_id']} | title: {parsed['title']}")
        print(f"    venue: {parsed['venue']} | competitors: {parsed['competitors']} | nations: {parsed['nations']}")
        print(f"    prev: {parsed['prev']} | next: {parsed['next']}\n")

    print("=" * 60)
    print("VERIFICATION TEST 3: 5 Team-Event Documents with Concatenated Medal Strings")
    print("=" * 60)
    for i, (doc, parsed) in enumerate(team_event_olympic, 1):
        print(f"[{i}] doc_id: {parsed['doc_id']} | title: {parsed['title']}")
        print(f"    gold:   '{parsed['gold']}'")
        print(f"    silver: '{parsed['silver']}'")
        print(f"    bronze: '{parsed['bronze']}'\n")

    print("=" * 60)
    print("VERIFICATION TEST 4: 5 Non-Olympic Distractor Documents")
    print("=" * 60)
    for i, (doc, parsed) in enumerate(non_olympic, 1):
        print(f"[{i}] doc_id: {parsed['doc_id']} | title: {parsed['title']}")
        print(f"    is_olympic_event: {parsed['is_olympic_event']} | infobox_type: {parsed['infobox_type']}\n")

    # Specific Assertion for concatenated medal string exact preservation
    test_concatenated_string = "Erik LesserDaniel BöhmArnd PeifferSimon Schempp"
    sample_raw_text = f"[Infobox Olympic event]\n  gold: {test_concatenated_string}\n"
    dummy_doc = {"doc_id": "TEST_Q0", "title": "Biathlon test", "text": sample_raw_text}
    parsed_dummy = parse_corpus_document(dummy_doc)
    
    print("=" * 60)
    print("EXPLICIT RAW MEDAL STRING PRESERVATION TEST")
    print("=" * 60)
    print(f"Expected: '{test_concatenated_string}'")
    print(f"Actual:   '{parsed_dummy['gold']}'")
    assert parsed_dummy["gold"] == test_concatenated_string, "FAIL: Raw medal string was altered!"
    print("PASS: Raw medal string preserved EXACTLY without modification or normalization.")
    print("=" * 60)


if __name__ == "__main__":
    run_verification()
