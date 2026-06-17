"""
loader.py — Load candidate profiles from JSONL or gzipped JSONL files.

Supports both .jsonl and .jsonl.gz formats.
Uses streaming to avoid loading the entire file into memory at once.
"""

import gzip
import json
import sys
from pathlib import Path


def load_candidates(filepath: str) -> list[dict]:
    """
    Load all candidate profiles from a JSONL or JSONL.GZ file.

    Args:
        filepath: Path to candidates.jsonl or candidates.jsonl.gz

    Returns:
        List of candidate dictionaries.
    """
    path = Path(filepath)

    if not path.exists():
        print(f"Error: File not found: {filepath}", file=sys.stderr)
        sys.exit(1)

    candidates = []
    open_fn = gzip.open if path.suffix == ".gz" else open

    try:
        with open_fn(path, "rt", encoding="utf-8") as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    candidate = json.loads(line)
                    candidates.append(candidate)
                except json.JSONDecodeError as e:
                    print(
                        f"Warning: Skipping malformed JSON at line {line_num}: {e}",
                        file=sys.stderr,
                    )
    except Exception as e:
        print(f"Error reading file {filepath}: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"Loaded {len(candidates):,} candidates from {path.name}")
    return candidates


def load_candidate_ids(filepath: str) -> set[str]:
    """
    Load just the candidate IDs from the file (for validation).

    Args:
        filepath: Path to candidates.jsonl or candidates.jsonl.gz

    Returns:
        Set of candidate_id strings.
    """
    path = Path(filepath)
    ids = set()
    open_fn = gzip.open if path.suffix == ".gz" else open

    with open_fn(path, "rt", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            data = json.loads(line)
            ids.add(data["candidate_id"])

    return ids
