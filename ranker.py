"""
ranker.py — Stage 5: Orchestrates all scoring stages and produces final ranking.

Pipeline:
1. Pre-filter (100K → subset)
2. Honeypot detection (flag traps)
3. Multi-dimensional base scoring
4. Behavioral signal modifier
5. Final score = base × behavioral
6. Sort, select top 100, generate reasoning
"""

import time

from prefilter import prefilter
from honeypot import detect_honeypots
from scorer import compute_base_score
from behavioral import compute_behavioral_modifier
from reasoning import generate_reasoning


def rank_candidates(candidates: list[dict], verbose: bool = False) -> list[dict]:
    """
    Run the full ranking pipeline on all candidates.

    Args:
        candidates: List of all candidate dicts from JSONL.
        verbose: If True, print detailed progress info.

    Returns:
        List of 100 dicts, each with:
        - candidate_id
        - rank (1-100)
        - score (float, non-increasing)
        - reasoning (string)
    """
    total_start = time.time()

    # ========================================================================
    # Stage 1: Pre-filter
    # ========================================================================
    stage_start = time.time()
    filtered = prefilter(candidates)
    if verbose:
        print(f"  Stage 1 (pre-filter): {time.time() - stage_start:.2f}s")

    # ========================================================================
    # Stage 3 (run early): Honeypot detection on ALL candidates
    # We detect honeypots on the filtered set to save time,
    # but we only need to ensure none sneak into top 100.
    # ========================================================================
    stage_start = time.time()
    honeypot_flags = detect_honeypots(filtered)
    if verbose:
        print(f"  Stage 3 (honeypots): {time.time() - stage_start:.2f}s")

    # ========================================================================
    # Stage 2 + 4: Score all filtered candidates
    # ========================================================================
    stage_start = time.time()
    scored_candidates = []

    for i, candidate in enumerate(filtered):
        cid = candidate.get("candidate_id", "")

        # Skip honeypots entirely — force them to score 0
        if cid in honeypot_flags:
            continue

        # Compute base score (multi-dimensional)
        base_score, breakdown = compute_base_score(candidate)

        # Apply behavioral modifier
        behavioral_mod, beh_breakdown = compute_behavioral_modifier(candidate)

        # Final score
        final_score = base_score * behavioral_mod

        scored_candidates.append({
            "candidate": candidate,
            "candidate_id": cid,
            "base_score": base_score,
            "behavioral_mod": behavioral_mod,
            "final_score": final_score,
            "score_breakdown": breakdown,
            "behavioral_breakdown": beh_breakdown,
        })

        if verbose and (i + 1) % 5000 == 0:
            print(f"    Scored {i + 1:,}/{len(filtered):,} candidates...")

    if verbose:
        print(f"  Stage 2+4 (scoring): {time.time() - stage_start:.2f}s")
        print(f"  Total scored: {len(scored_candidates):,} "
              f"(after removing {len(honeypot_flags)} honeypots)")

    # ========================================================================
    # Stage 5: Sort and select top 100
    # ========================================================================
    stage_start = time.time()

    # Sort by final_score descending, then by candidate_id ascending for ties
    scored_candidates.sort(
        key=lambda x: (-x["final_score"], x["candidate_id"])
    )

    # Take top 100
    top_100 = scored_candidates[:100]

    if verbose:
        print(f"  Stage 5 (ranking): {time.time() - stage_start:.2f}s")

    # ========================================================================
    # Stage 6: Generate reasoning for each of the top 100
    # ========================================================================
    stage_start = time.time()
    results = []

    for rank, entry in enumerate(top_100, start=1):
        reasoning = generate_reasoning(
            candidate=entry["candidate"],
            rank=rank,
            final_score=entry["final_score"],
            score_breakdown=entry["score_breakdown"],
        )

        results.append({
            "candidate_id": entry["candidate_id"],
            "rank": rank,
            "score": entry["final_score"],  # Keep full precision for now
            "reasoning": reasoning,
        })

    # Post-process: ensure all scores are unique and properly ordered.
    # The validator requires:
    # 1. Scores non-increasing with rank
    # 2. Equal scores must have candidate_id ascending
    #
    # Strategy: re-sort by (score desc, candidate_id asc), then assign
    # monotonically decreasing scores using a small epsilon.
    results.sort(key=lambda x: (-x["score"], x["candidate_id"]))

    # Re-assign ranks after proper sort
    for i, r in enumerate(results):
        r["rank"] = i + 1

    # Ensure scores are strictly decreasing to avoid tie-break issues
    for i in range(1, len(results)):
        if results[i]["score"] >= results[i - 1]["score"]:
            results[i]["score"] = results[i - 1]["score"] - 0.000001

    if verbose:
        print(f"  Stage 6 (reasoning): {time.time() - stage_start:.2f}s")

    total_elapsed = time.time() - total_start
    print(f"\nTotal pipeline time: {total_elapsed:.2f}s")

    # Print summary of top 10
    print("\n=== Top 10 Candidates ===")
    for r in results[:10]:
        print(f"  Rank {r['rank']:>3}: {r['candidate_id']} "
              f"(score: {r['score']:.4f}) — {r['reasoning'][:80]}...")

    # Print score distribution
    scores = [r["score"] for r in results]
    print(f"\nScore range: {min(scores):.4f} — {max(scores):.4f}")
    print(f"Median score: {scores[49]:.4f}")

    return results
