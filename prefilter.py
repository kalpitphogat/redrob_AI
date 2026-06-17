"""
prefilter.py — Stage 1: Fast pre-filtering to reduce candidate pool.

Eliminates obviously unfit candidates before detailed scoring.
Goal: 100K candidates → ~5K-15K candidates for deeper analysis.

The pre-filter is intentionally generous to avoid false negatives.
A candidate only gets eliminated if they are clearly not a fit
across MULTIPLE dimensions simultaneously.
"""

from config import (
    PREFILTER_MIN_EXPERIENCE,
    PREFILTER_MAX_EXPERIENCE,
    TITLE_SCORES,
    NON_TECH_SKILLS,
    MUST_HAVE_SKILLS,
    STRONG_WANT_SKILLS,
    NICE_TO_HAVE_SKILLS,
)


def _get_title_score(title: str) -> float:
    """Look up title score, trying exact match then fuzzy containment."""
    title_lower = title.lower().strip()

    # Exact match
    if title_lower in TITLE_SCORES:
        return TITLE_SCORES[title_lower]

    # Check if any known title is contained in the candidate's title
    best_score = 0.0
    for known_title, score in TITLE_SCORES.items():
        if known_title in title_lower or title_lower in known_title:
            best_score = max(best_score, score)

    return best_score


def _has_any_relevant_skills(candidate: dict) -> bool:
    """Check if the candidate has ANY skill remotely related to tech/AI/ML."""
    all_relevant = MUST_HAVE_SKILLS | STRONG_WANT_SKILLS | NICE_TO_HAVE_SKILLS
    skills = candidate.get("skills", [])

    for skill in skills:
        skill_name = skill.get("name", "").lower().strip()
        for relevant in all_relevant:
            if relevant in skill_name or skill_name in relevant:
                return True

    return False


def _has_technical_career_history(candidate: dict) -> bool:
    """
    Check if any career history entry has a technical title,
    even if the current title is non-technical.
    """
    career = candidate.get("career_history", [])
    technical_keywords = [
        "engineer", "developer", "scientist", "architect",
        "ml", "ai", "data", "software", "backend", "frontend",
        "devops", "sre", "platform", "research",
    ]

    for role in career:
        role_title = role.get("title", "").lower()
        for kw in technical_keywords:
            if kw in role_title:
                return True

    return False


def _count_non_tech_skills_ratio(candidate: dict) -> float:
    """
    Compute the ratio of non-tech skills to total skills.
    A high ratio suggests a non-technical candidate.
    """
    skills = candidate.get("skills", [])
    if not skills:
        return 0.0

    non_tech_count = 0
    for skill in skills:
        skill_name = skill.get("name", "").lower().strip()
        if skill_name in NON_TECH_SKILLS:
            non_tech_count += 1

    return non_tech_count / len(skills)


def prefilter(candidates: list[dict]) -> list[dict]:
    """
    Apply fast pre-filtering to eliminate obviously unfit candidates.

    A candidate passes if they meet ANY of these criteria:
    - Has a technical title (score > 0.1)
    - Has relevant skills AND technical career history
    - Has a good title score (> 0.3) regardless of other factors

    A candidate is eliminated only if ALL of these are true:
    - Title score is very low (< 0.05)
    - No relevant technical skills
    - No technical career history
    - OR experience is way out of range

    Returns:
        Filtered list of candidates that passed pre-filtering.
    """
    passed = []
    eliminated = 0

    for candidate in candidates:
        profile = candidate.get("profile", {})
        current_title = profile.get("current_title", "")
        years_exp = profile.get("years_of_experience", 0)

        # --- Hard elimination: experience completely out of range ---
        if years_exp < PREFILTER_MIN_EXPERIENCE or years_exp > PREFILTER_MAX_EXPERIENCE:
            eliminated += 1
            continue

        # --- Title-based fast pass ---
        title_score = _get_title_score(current_title)

        # Strong titles pass immediately
        if title_score >= 0.30:
            passed.append(candidate)
            continue

        # --- For weak titles, check other signals ---
        has_skills = _has_any_relevant_skills(candidate)
        has_tech_career = _has_technical_career_history(candidate)
        non_tech_ratio = _count_non_tech_skills_ratio(candidate)

        # Pass if they have relevant skills OR a technical career history
        if has_skills or has_tech_career:
            passed.append(candidate)
            continue

        # Pass if title score is at least moderate (e.g., business analyst
        # who might have technical depth)
        if title_score >= 0.05:
            passed.append(candidate)
            continue

        # Eliminate: non-technical title + no relevant skills + no tech career
        eliminated += 1

    print(f"Pre-filter: {len(candidates):,} -> {len(passed):,} "
          f"(eliminated {eliminated:,})")
    return passed
