"""
loader.py — Load candidate profiles from JSONL, JSON array, or gzipped variants.

Supports:
  - candidates.jsonl          (one JSON object per line)
  - candidates.jsonl.gz       (gzipped JSONL)
  - sample_candidates.json    (a JSON array [{}...])
  - candidates.json.gz        (gzipped JSON array)

Uses streaming for JSONL to avoid loading the entire file into memory at once.
"""

import gzip
import json
import sys
from pathlib import Path


def load_candidates(filepath: str) -> list[dict]:
    """
    Load all candidate profiles from a JSONL, JSON array, or gzipped variant.

    Args:
        filepath: Path to candidates file (.jsonl, .json, .jsonl.gz, .json.gz)

    Returns:
        List of candidate dictionaries.
    """
    path = Path(filepath)

    if not path.exists():
        print(f"Error: File not found: {filepath}", file=sys.stderr)
        sys.exit(1)

    open_fn = gzip.open if path.suffix == ".gz" else open
    candidates = []

    try:
        with open_fn(path, "rt", encoding="utf-8") as f:
            # Peek at the first non-whitespace character to detect format
            raw = f.read()

        stripped = raw.lstrip()

        if stripped.startswith("["):
            # ── JSON array format: [{...}, {...}, ...] ────────────────────────
            try:
                candidates = json.loads(raw)
                if not isinstance(candidates, list):
                    raise ValueError("Top-level JSON is not a list")
            except (json.JSONDecodeError, ValueError) as e:
                print(f"Error parsing JSON array from {filepath}: {e}", file=sys.stderr)
                sys.exit(1)
        else:
            # ── JSONL format: one JSON object per line ────────────────────────
            for line_num, line in enumerate(raw.splitlines(), 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    candidates.append(json.loads(line))
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
