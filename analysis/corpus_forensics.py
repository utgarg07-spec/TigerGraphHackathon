"""
Corpus Forensics and Dataset Processing for Phase 1.

Processes all 2,951 documents in data/corpus.jsonl using analysis.infobox_parser.
Generates:
- data/processed/events.jsonl (parsed Olympic event records)
- analysis/reports/corpus_forensics.json (exact forensic stats)
"""

import json
import os
import sys
from collections import Counter
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from analysis.infobox_parser import parse_corpus_document


def run_corpus_forensics(
    corpus_path: str = "data/corpus.jsonl",
    events_output_path: str = "data/processed/events.jsonl",
    report_output_path: str = "analysis/reports/corpus_forensics.json",
):
    corpus_file = Path(corpus_path)
    if not corpus_file.exists():
        raise FileNotFoundError(f"Corpus file not found: {corpus_path}")

    # Ensure output directories exist
    Path(events_output_path).parent.mkdir(parents=True, exist_ok=True)
    Path(report_output_path).parent.mkdir(parents=True, exist_ok=True)

    total_documents = 0
    doc_ids = set()
    duplicate_doc_ids = []
    titles = set()
    duplicate_titles = []

    infobox_type_counts = Counter()
    olympic_event_docs = []
    non_olympic_docs = []

    parse_failures = []
    malformed_numeric_docs = []
    unusual_formatting_docs = []

    # Target Olympic fields for coverage report
    target_fields = [
        "event",
        "games",
        "venue",
        "date_raw",
        "competitors",
        "nations",
        "gold",
        "goldNOC",
        "silver",
        "silverNOC",
        "bronze",
        "bronzeNOC",
        "win_value",
        "prev",
        "next",
    ]

    field_present_counts = Counter()

    with open(corpus_file, "r", encoding="utf-8") as f_in, open(
        events_output_path, "w", encoding="utf-8"
    ) as f_events:

        for line_no, line in enumerate(f_in, 1):
            total_documents += 1
            raw_doc = json.loads(line)
            doc_id = raw_doc.get("doc_id")
            title = raw_doc.get("title")

            # Duplicate checks
            if doc_id in doc_ids:
                duplicate_doc_ids.append(doc_id)
            else:
                doc_ids.add(doc_id)

            if title in titles:
                duplicate_titles.append(title)
            else:
                titles.add(title)

            parsed = parse_corpus_document(raw_doc)
            ib_type = parsed["infobox_type"] or "NO_INFOBOX"
            infobox_type_counts[ib_type] += 1

            if parsed["is_olympic_event"]:
                olympic_event_docs.append(parsed)

                # Validation checks for Olympic event parsing
                if not parsed["event"] or not parsed["games"]:
                    parse_failures.append(
                        {
                            "doc_id": doc_id,
                            "title": title,
                            "reason": "Missing required event or games field in Olympic infobox",
                        }
                    )

                # Check field coverage
                for f_name in target_fields:
                    if parsed.get(f_name) is not None:
                        field_present_counts[f_name] += 1

                # Check malformed numerics in raw fields vs parsed int
                raw_fields = parsed.get("raw_fields", {})
                for num_key in ["competitors", "nations", "prev", "next"]:
                    raw_val = raw_fields.get(num_key)
                    parsed_val = parsed.get(num_key)
                    if raw_val is not None and raw_val != "" and parsed_val is None:
                        malformed_numeric_docs.append(
                            {
                                "doc_id": doc_id,
                                "field": num_key,
                                "raw_value": raw_val,
                            }
                        )

                # Check unusual field formatting
                if raw_fields.get("venues") or raw_fields.get("dates") or raw_fields.get("bronze2"):
                    unusual_formatting_docs.append(
                        {
                            "doc_id": doc_id,
                            "title": title,
                            "unusual_keys": [
                                k
                                for k in ["venues", "dates", "bronze2", "gold2"]
                                if k in raw_fields
                            ],
                        }
                    )

                # Write to events.jsonl
                # Exclude raw_fields helper dict from events.jsonl output
                clean_event_record = {
                    "doc_id": parsed["doc_id"],
                    "title": parsed["title"],
                    "is_olympic_event": parsed["is_olympic_event"],
                    "infobox_type": parsed["infobox_type"],
                    "event": parsed["event"],
                    "games": parsed["games"],
                    "sport": parsed["sport"],
                    "venue": parsed["venue"],
                    "date_raw": parsed["date_raw"],
                    "competitors": parsed["competitors"],
                    "nations": parsed["nations"],
                    "gold": parsed["gold"],
                    "goldNOC": parsed["goldNOC"],
                    "silver": parsed["silver"],
                    "silverNOC": parsed["silverNOC"],
                    "bronze": parsed["bronze"],
                    "bronzeNOC": parsed["bronzeNOC"],
                    "win_value": parsed["win_value"],
                    "prev": parsed["prev"],
                    "next": parsed["next"],
                }
                f_events.write(json.dumps(clean_event_record, ensure_ascii=False) + "\n")
            else:
                non_olympic_docs.append(parsed)

    total_olympic = len(olympic_event_docs)
    total_non_olympic = len(non_olympic_docs)

    # Calculate exact field coverage stats
    field_coverage = {}
    for f_name in target_fields:
        present = field_present_counts[f_name]
        missing = total_olympic - present
        percentage = round((present / total_olympic) * 100, 2) if total_olympic > 0 else 0.0
        field_coverage[f_name] = {
            "present": present,
            "percentage": percentage,
            "missing": missing,
        }

    forensics_report = {
        "total_documents": total_documents,
        "olympic_event_documents": total_olympic,
        "olympic_event_percentage": round((total_olympic / total_documents) * 100, 2),
        "non_olympic_documents": total_non_olympic,
        "non_olympic_percentage": round((total_non_olympic / total_documents) * 100, 2),
        "infobox_type_distribution": dict(infobox_type_counts.most_common()),
        "olympic_field_coverage": field_coverage,
        "duplicates": {
            "duplicate_doc_ids_count": len(duplicate_doc_ids),
            "duplicate_doc_ids": duplicate_doc_ids,
            "duplicate_titles_count": len(duplicate_titles),
            "duplicate_titles": duplicate_titles,
        },
        "parse_failures": {
            "failed_olympic_parsing_count": len(parse_failures),
            "parse_failures": parse_failures,
            "malformed_numeric_count": len(malformed_numeric_docs),
            "malformed_numeric_samples": malformed_numeric_docs[:10],
            "unusual_formatting_count": len(unusual_formatting_docs),
            "unusual_formatting_samples": unusual_formatting_docs[:10],
        },
    }

    with open(report_output_path, "w", encoding="utf-8") as f_rep:
        json.dump(forensics_report, f_rep, indent=2, ensure_ascii=False)

    print("=" * 60)
    print("CORPUS FORENSICS REPORT SUMMARY")
    print("=" * 60)
    print(f"Total documents processed:       {total_documents}")
    print(f"Olympic event documents:         {total_olympic} ({forensics_report['olympic_event_percentage']}%)")
    print(f"Non-Olympic distractor docs:    {total_non_olympic} ({forensics_report['non_olympic_percentage']}%)")
    print(f"Duplicate doc IDs:               {len(duplicate_doc_ids)}")
    print(f"Duplicate titles:                {len(duplicate_titles)}")
    print(f"Olympic parse failures:          {len(parse_failures)}")
    print(f"Malformed numeric values:        {len(malformed_numeric_docs)}")
    print("\nInfobox Type Distribution (Top 10):")
    for k, v in list(infobox_type_counts.most_common(10)):
        print(f"  - {k:35s}: {v}")

    print("\nOlympic Field Coverage:")
    for f_name, stats in field_coverage.items():
        print(
            f"  - {f_name:15s}: {stats['present']:5d} present ({stats['percentage']:6.2f}%) | {stats['missing']:5d} missing"
        )

    print("=" * 60)
    print(f"Events JSONL written to: {events_output_path}")
    print(f"Forensics JSON report written to: {report_output_path}")
    print("=" * 60)

    return forensics_report


if __name__ == "__main__":
    run_corpus_forensics()
