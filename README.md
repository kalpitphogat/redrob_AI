# Redrob Candidate Ranking System

**Intelligent Candidate Discovery & Ranking Challenge**  
Submission for the Redrob Hackathon

## Overview

Rule-based multi-dimensional ranking system that identifies the top 100 candidates for a Senior AI Engineer role from a 100,000-candidate pool. Designed to avoid keyword-stuffer traps and honeypot candidates by using trust-weighted skill scoring, career trajectory analysis, and behavioral signal modifiers.

## Architecture

Six-stage pipeline:

1. **Pre-filter** — Fast elimination of obviously unfit candidates (100K → ~15K-30K)
2. **Honeypot Detection** — Identifies ~80 trap candidates with impossible profiles
3. **Multi-dimensional Scoring** — Six weighted dimensions:
   - Title & Career Trajectory (30%)
   - Skills Match with trust weighting (25%)
   - Career Description Analysis (15%)
   - Experience Band Fit (15%)
   - Location Proximity (10%)
   - Education (5%)
4. **Behavioral Signal Modifier** — Multiplicative adjustment based on platform engagement
5. **Final Ranking** — Sort, select top 100, assign ranks
6. **Reasoning Generation** — Specific, fact-grounded reasoning per candidate

## Quick Start

### Prerequisites
- Python 3.10+
- No external dependencies (uses only Python standard library)

### Reproduce the Submission

```bash
python rank.py --candidates ./candidates.jsonl --out ./submission.csv
```

With verbose output:
```bash
python rank.py --candidates ./candidates.jsonl --out ./submission.csv --verbose
```

### Validate the Submission
```bash
python validate_submission.py submission.csv
```

## File Structure

```
├── rank.py              # Main entry point (single command)
├── config.py            # All tunable weights, thresholds, keyword lists
├── loader.py            # JSONL/JSONL.GZ candidate loader
├── prefilter.py         # Stage 1: Fast pre-filtering
├── scorer.py            # Stage 2: Multi-dimensional scoring
├── honeypot.py          # Stage 3: Honeypot detection
├── behavioral.py        # Stage 4: Behavioral signal modifiers
├── ranker.py            # Stage 5: Pipeline orchestration
├── reasoning.py         # Stage 6: Reasoning generation
├── requirements.txt     # Dependencies (stdlib only)
└── README.md            # This file
```

## Design Decisions

### Why rule-based instead of ML/embeddings?

1. **No training data**: No ground-truth labels to train a model on
2. **Compute constraints**: 5 min CPU, 16GB RAM, no GPU, no network
3. **JD has explicit criteria**: The JD provides detailed, explicit ranking criteria (experience bands, location preferences, disqualifiers, skill priorities) — encoding these faithfully beats a statistical approach
4. **Trap awareness**: The dataset contains keyword stuffers and honeypots designed to fool embedding-based cosine similarity approaches

### How honeypots are caught

- Salary min > max inversions
- Expert proficiency in many skills with 0 duration months
- Assessment scores contradicting claimed proficiency
- Impossible date arithmetic in career history
- Signup date after last active date

### How keyword stuffers are avoided

The scoring system uses **trust-weighted skills** where each skill's contribution is modified by:
- `proficiency × duration_months × endorsements → trust_score`
- Expert claims with 0 duration get 80% penalty
- Expert claims with 0 endorsements and <6 months get 90% penalty
- Non-technical titles with many AI skills get down-weighted

### Behavioral signals integration

Following the JD's explicit guidance: "a perfect-on-paper candidate who hasn't logged in for 6 months and has a 5% recruiter response rate is not actually available."

All behavioral signals are multiplicative modifiers (0.3x to 1.3x) applied after the base content-match score.

## Compute Profile

- **Runtime**: ~30-60 seconds on modern CPU
- **Memory**: <2 GB peak
- **Dependencies**: Python standard library only
- **Network**: None

## Methodology Summary

Rule-based ranker with trust-weighted skill scoring and behavioral signal modifiers. Six scoring dimensions (title/career 30%, skills 25%, career descriptions 15%, experience 15%, location 10%, education 5%) combined multiplicatively with an 11-signal behavioral modifier. Title and career trajectory serve as the primary discriminator against keyword-stuffer traps. Honeypot detection uses five anomaly checks (salary inversion, expert-skill inflation, assessment contradictions, impossible dates, signup-after-active). Runtime is ~30-60 seconds for 100K candidates on CPU.
