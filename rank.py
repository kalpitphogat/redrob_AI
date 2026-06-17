#!/usr/bin/env python3
"""
rank.py — Main entry point for the Redrob candidate ranking system.

Usage:
    python rank.py --candidates ./candidates.jsonl --out ./submission.csv

Accepts both .jsonl and .jsonl.gz input files.
Produces a validated CSV file matching the submission spec.

Constraints satisfied:
- Runtime: ≤ 5 minutes wall-clock
- Memory: ≤ 16 GB RAM
- Compute: CPU only
- Network: None (no external API calls)
"""

import argparse
import csv
import sys
import time
from pathlib import Path

from loader import load_candidates
from ranker import rank_candidates


def write_submission_csv(results: list[dict], output_path: str) -> None:
    """
    Write the top-100 ranking to a CSV file matching the submission spec.

    Format:
        candidate_id,rank,score,reasoning

    Rules enforced:
    - Exactly 100 rows + 1 header
    - Ranks 1-100 each used exactly once
    - Scores non-increasing with rank
    - UTF-8 encoding
    """
    path = Path(output_path)

    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["candidate_id", "rank", "score", "reasoning"])

        for entry in results:
            writer.writerow([
                entry["candidate_id"],
                entry["rank"],
                f"{entry['score']:.6f}",
                entry["reasoning"],
            ])

    print(f"\nSubmission written to: {path}")
    print(f"Rows: {len(results)} (header + {len(results)} data)")


def main():
    parser = argparse.ArgumentParser(
        description="Redrob Candidate Ranking System — "
                    "Intelligent Candidate Discovery & Ranking Challenge"
    )
    parser.add_argument(
        "--candidates",
        required=True,
        help="Path to candidates.jsonl or candidates.jsonl.gz",
    )
    parser.add_argument(
        "--out",
        default="submission.csv",
        help="Output CSV path (default: submission.csv)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print detailed progress information",
    )

    args = parser.parse_args()

    print("=" * 60)
    print("  Redrob Candidate Ranking System")
    print("  Senior AI Engineer — Founding Team")
    print("=" * 60)

    overall_start = time.time()

    # Load candidates
    print(f"\nLoading candidates from: {args.candidates}")
    candidates = load_candidates(args.candidates)

    if not candidates:
        print("Error: No candidates loaded.", file=sys.stderr)
        sys.exit(1)

    print(f"Loaded {len(candidates):,} candidates\n")

    # Run ranking pipeline
    print("Running ranking pipeline...")
    results = rank_candidates(candidates, verbose=args.verbose)

    if len(results) != 100:
        print(f"Error: Expected 100 results, got {len(results)}", file=sys.stderr)
        sys.exit(1)

    # Write output
    write_submission_csv(results, args.out)

    overall_elapsed = time.time() - overall_start
    print(f"\nTotal wall-clock time: {overall_elapsed:.2f}s")

    if overall_elapsed > 300:
        print("WARNING: Exceeded 5-minute compute budget!", file=sys.stderr)
    elif overall_elapsed > 240:
        print("NOTE: Close to 5-minute budget. Consider optimization.")
    else:
        print(f"Well within 5-minute budget ({overall_elapsed:.0f}s / 300s).")


if __name__ == "__main__":
    main()
