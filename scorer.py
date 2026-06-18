"""
scorer.py — Stage 2: Multi-dimensional candidate scoring engine.

Computes a base score (0-1) for each candidate across six dimensions:
1. Title & Career Trajectory (30%)
2. Skills Match with trust weighting (25%)
3. Career Description Analysis (15%)
4. Experience Band Fit (15%)
5. Location Proximity (10%)
6. Education (5%)

The scoring is designed to reward genuine AI/ML engineers with
production experience, NOT keyword stuffers with inflated skill lists.
"""

import config
from config import (
    TITLE_SCORES,
    MUST_HAVE_SKILLS,
    STRONG_WANT_SKILLS,
    NICE_TO_HAVE_SKILLS,
    SKILL_CATEGORY_POINTS,
    NON_TECH_SKILLS,
    CONSULTING_FIRMS,
    PRODUCT_COMPANIES,
    LOCATION_TIER_SCORES,
    INDIA_OTHER_RELOCATE,
    INDIA_OTHER_NO_RELOCATE,
    OUTSIDE_INDIA_RELOCATE,
    OUTSIDE_INDIA_NO_RELOCATE,
    INDIA_COUNTRY,
    EXPERIENCE_IDEAL_MIN,
    EXPERIENCE_IDEAL_MAX,
    EXPERIENCE_ACCEPTABLE_MIN,
    EXPERIENCE_ACCEPTABLE_MAX,
    EXPERIENCE_HARD_MIN,
    EXPERIENCE_HARD_MAX,
    STRONG_POSITIVE_KEYWORDS,
    MODERATE_POSITIVE_KEYWORDS,
    NEGATIVE_CAREER_KEYWORDS,
)


# ============================================================================
# Dimension 1: Title & Career Trajectory (30%)
# ============================================================================

def _score_title(title: str) -> float:
    """Score the candidate's current title against the JD."""
    title_lower = title.lower().strip()

    # Exact match
    if title_lower in TITLE_SCORES:
        return TITLE_SCORES[title_lower]

    # Containment match (e.g., "Senior AI/ML Engineer" contains "ai engineer")
    best = 0.0
    for known, score in TITLE_SCORES.items():
        if known in title_lower or title_lower in known:
            best = max(best, score)

    # Partial keyword match for titles not in our map
    if best == 0.0:
        title_words = set(title_lower.split())
        tech_words = {"engineer", "developer", "scientist", "architect", "researcher"}
        ai_words = {"ai", "ml", "machine", "learning", "data", "nlp", "deep"}
        if title_words & tech_words:
            best = 0.35
            if title_words & ai_words:
                best = 0.60
        else:
            best = 0.05

    return best


def _score_career_trajectory(candidate: dict) -> float:
    """
    Analyze the career trajectory:
    - Company types (product vs consulting)
    - Title progression
    - Career stability (avg tenure)
    - Industry relevance
    """
    career = candidate.get("career_history", [])
    if not career:
        return 0.1

    scores = []
    total_months = 0
    consulting_months = 0
    product_months = 0
    tech_roles = 0

    for role in career:
        company = role.get("company", "").lower()
        title = role.get("title", "").lower()
        duration = role.get("duration_months", 0)
        industry = role.get("industry", "").lower()

        total_months += duration

        # Check company type
        is_consulting = any(cf in company for cf in CONSULTING_FIRMS)
        is_product = any(pc in company for pc in PRODUCT_COMPANIES)

        if is_consulting:
            consulting_months += duration
        if is_product:
            product_months += duration

        # Check if this is a technical role
        role_score = _score_title(title)
        if role_score >= 0.30:
            tech_roles += 1

        scores.append(role_score)

    # Career trajectory score components
    trajectory_score = 0.0

    # 1. Average technical level of roles (weight: 40% of trajectory)
    avg_title_score = sum(scores) / len(scores) if scores else 0
    trajectory_score += 0.4 * avg_title_score

    # 2. Best role (weight: 30% — rewards anyone who's held a strong role)
    best_title_score = max(scores) if scores else 0
    trajectory_score += 0.3 * best_title_score

    # 3. Company type (weight: 20%)
    if total_months > 0:
        consulting_ratio = consulting_months / total_months
        product_ratio = product_months / total_months

        # JD explicitly flags entire-career-at-consulting
        if consulting_ratio >= 0.95:
            company_score = 0.1  # Strong penalty
        elif consulting_ratio >= 0.7:
            company_score = 0.3
        elif product_ratio >= 0.5:
            company_score = 0.9  # Product company bonus
        else:
            company_score = 0.5  # Mixed — neutral
    else:
        company_score = 0.3

    trajectory_score += 0.2 * company_score

    # 4. Career stability (weight: 10%)
    num_roles = len(career)
    total_years = total_months / 12 if total_months > 0 else 1
    avg_tenure_years = total_years / num_roles if num_roles > 0 else 0

    if avg_tenure_years >= 3.0:
        stability = 1.0  # Very stable
    elif avg_tenure_years >= 2.0:
        stability = 0.8
    elif avg_tenure_years >= 1.5:
        stability = 0.5  # JD warns about 1.5-year hoppers
    else:
        stability = 0.2  # Title-chaser pattern

    trajectory_score += 0.1 * stability

    return min(1.0, trajectory_score)


def score_title_career(candidate: dict) -> float:
    """Combined title + career trajectory score."""
    profile = candidate.get("profile", {})
    current_title = profile.get("current_title", "")

    title_score = _score_title(current_title)
    trajectory_score = _score_career_trajectory(candidate)

    # Weighted combination: current title matters more
    return 0.55 * title_score + 0.45 * trajectory_score


# ============================================================================
# Dimension 2: Skills Match (25%)
# ============================================================================

def _skill_trust_weight(skill: dict) -> float:
    """
    Compute a trust weight for a single skill based on:
    - proficiency level
    - duration_months (how long they've used it)
    - endorsements (social validation)

    Returns a value 0.0 to 1.0 representing how much we trust this claim.
    """
    proficiency_map = {
        "expert": 1.0,
        "advanced": 0.75,
        "intermediate": 0.50,
        "beginner": 0.25,
    }

    prof = skill.get("proficiency", "beginner").lower()
    duration = skill.get("duration_months", 0)
    endorsements = skill.get("endorsements", 0)

    prof_score = proficiency_map.get(prof, 0.25)

    # Duration trust: 0-6 months = low, 6-24 = medium, 24+ = high
    if duration >= 24:
        duration_trust = 1.0
    elif duration >= 12:
        duration_trust = 0.7
    elif duration >= 6:
        duration_trust = 0.4
    else:
        duration_trust = 0.15

    # Endorsement trust: logarithmic scale
    if endorsements >= 20:
        endorse_trust = 1.0
    elif endorsements >= 10:
        endorse_trust = 0.7
    elif endorsements >= 3:
        endorse_trust = 0.4
    else:
        endorse_trust = 0.15

    # Combined trust = weighted average
    trust = 0.4 * prof_score + 0.35 * duration_trust + 0.25 * endorse_trust

    # Penalty: Expert/Advanced with 0 duration = suspicious
    if prof in ("expert", "advanced") and duration == 0:
        trust *= 0.2

    # Penalty: Expert with 0 endorsements and < 6 months
    if prof == "expert" and endorsements == 0 and duration < 6:
        trust *= 0.1

    return trust


def _match_skill_to_category(skill_name: str) -> tuple[str, float]:
    """
    Match a skill name to our taxonomy categories.
    Returns (category, base_points).
    """
    name_lower = skill_name.lower().strip()

    # Check must-have
    for s in MUST_HAVE_SKILLS:
        if s in name_lower or name_lower in s:
            return "must_have", SKILL_CATEGORY_POINTS["must_have"]

    # Check strong-want
    for s in STRONG_WANT_SKILLS:
        if s in name_lower or name_lower in s:
            return "strong_want", SKILL_CATEGORY_POINTS["strong_want"]

    # Check nice-to-have
    for s in NICE_TO_HAVE_SKILLS:
        if s in name_lower or name_lower in s:
            return "nice_to_have", SKILL_CATEGORY_POINTS["nice_to_have"]

    return "other", 0.0


def score_skills(candidate: dict) -> float:
    """
    Score skill-JD alignment with trust weighting.

    The system rewards:
    - Must-have skills with high trust (long duration, endorsements)
    - Breadth across skill categories
    - Skills backed by career history

    The system penalizes:
    - Keyword stuffing (many expert skills, low trust)
    - Skills that don't match career history
    """
    skills = candidate.get("skills", [])

    if not skills:
        return 0.0

    total_weighted_points = 0.0
    must_have_count = 0
    strong_want_count = 0
    nice_to_have_count = 0
    non_tech_count = 0
    matched_categories = set()

    for skill in skills:
        skill_name = skill.get("name", "")
        name_lower = skill_name.lower().strip()

        # Check if it's a non-tech skill
        if name_lower in NON_TECH_SKILLS:
            non_tech_count += 1
            continue

        category, base_points = _match_skill_to_category(skill_name)
        if base_points == 0:
            continue

        trust = _skill_trust_weight(skill)
        weighted = base_points * trust

        total_weighted_points += weighted
        matched_categories.add(category)

        if category == "must_have":
            must_have_count += 1
        elif category == "strong_want":
            strong_want_count += 1
        elif category == "nice_to_have":
            nice_to_have_count += 1

    # Normalize score
    # Max theoretical: 5 must-haves × 5.0 × 1.0 = 25, but realistic max ~15
    raw_score = total_weighted_points / 18.0

    # Bonus for breadth (having skills across multiple categories)
    if len(matched_categories) >= 3:
        raw_score *= 1.15
    elif len(matched_categories) >= 2:
        raw_score *= 1.05

    # Bonus for must-have coverage (most important)
    if must_have_count >= 3:
        raw_score *= 1.20
    elif must_have_count >= 2:
        raw_score *= 1.10

    # Penalty for high non-tech ratio (suggests non-technical background)
    total_skills = len(skills)
    if total_skills > 0:
        non_tech_ratio = non_tech_count / total_skills
        if non_tech_ratio > 0.6:
            raw_score *= 0.3
        elif non_tech_ratio > 0.4:
            raw_score *= 0.6

    return min(1.0, raw_score)


# ============================================================================
# Dimension 3: Career Description Analysis (15%)
# ============================================================================

def score_career_descriptions(candidate: dict) -> float:
    """
    Analyze career history descriptions for relevant keywords.

    NOTE: The dataset uses recycled description templates, so this
    dimension has intentionally lower weight. We use it as supplementary
    signal, not primary.
    """
    career = candidate.get("career_history", [])

    if not career:
        return 0.0

    # Also include the profile summary
    profile = candidate.get("profile", {})
    summary = profile.get("summary", "").lower()

    strong_hits = 0
    moderate_hits = 0
    negative_hits = 0

    texts = [summary]
    for role in career:
        desc = role.get("description", "").lower()
        texts.append(desc)

    combined_text = " ".join(texts)

    for keyword in STRONG_POSITIVE_KEYWORDS:
        if keyword in combined_text:
            strong_hits += 1

    for keyword in MODERATE_POSITIVE_KEYWORDS:
        if keyword in combined_text:
            moderate_hits += 1

    for keyword in NEGATIVE_CAREER_KEYWORDS:
        if keyword in combined_text:
            negative_hits += 1

    # Score: positive keywords add, negative keywords subtract
    raw = (strong_hits * 3.0 + moderate_hits * 1.0 - negative_hits * 1.5)

    # Normalize: theoretical max around 20-30 strong + moderate hits
    normalized = raw / 15.0

    # Clamp to [0, 1]
    return max(0.0, min(1.0, normalized))


# ============================================================================
# Dimension 4: Experience Band Fit (15%)
# ============================================================================

def score_experience(candidate: dict) -> float:
    """
    Score based on years of experience.
    JD says 5-9 years ideal, flexible for strong candidates.
    """
    profile = candidate.get("profile", {})
    years = profile.get("years_of_experience", 0)

    if EXPERIENCE_IDEAL_MIN <= years <= EXPERIENCE_IDEAL_MAX:
        return 1.0
    elif years < EXPERIENCE_IDEAL_MIN:
        # Below ideal range
        if years >= EXPERIENCE_ACCEPTABLE_MIN:
            # 3-5 years: linearly ramp from 0.5 to 1.0
            return 0.5 + 0.5 * (years - EXPERIENCE_ACCEPTABLE_MIN) / \
                   (EXPERIENCE_IDEAL_MIN - EXPERIENCE_ACCEPTABLE_MIN)
        elif years >= EXPERIENCE_HARD_MIN:
            # 1.5-3 years: low score
            return 0.2 + 0.3 * (years - EXPERIENCE_HARD_MIN) / \
                   (EXPERIENCE_ACCEPTABLE_MIN - EXPERIENCE_HARD_MIN)
        else:
            return 0.05
    else:
        # Above ideal range
        if years <= EXPERIENCE_ACCEPTABLE_MAX:
            # 9-14 years: gentle decline
            return 1.0 - 0.4 * (years - EXPERIENCE_IDEAL_MAX) / \
                   (EXPERIENCE_ACCEPTABLE_MAX - EXPERIENCE_IDEAL_MAX)
        elif years <= EXPERIENCE_HARD_MAX:
            # 14-20 years: steeper decline (JD says "this role writes code")
            return 0.3 - 0.2 * (years - EXPERIENCE_ACCEPTABLE_MAX) / \
                   (EXPERIENCE_HARD_MAX - EXPERIENCE_ACCEPTABLE_MAX)
        else:
            return 0.05


# ============================================================================
# Dimension 5: Location (10%)
# ============================================================================

def score_location(candidate: dict) -> float:
    """
    Score based on geographic fit.
    JD: Pune/Noida preferred, Tier-1 Indian cities welcome,
    outside India case-by-case.
    """
    profile = candidate.get("profile", {})
    signals = candidate.get("redrob_signals", {})

    location = profile.get("location", "").lower().strip()
    country = profile.get("country", "").lower().strip()
    willing_to_relocate = signals.get("willing_to_relocate", False)

    # Check if location matches any known city
    for city, score in LOCATION_TIER_SCORES.items():
        if city in location:
            return score

    # Didn't match a known city — check country
    if country == INDIA_COUNTRY or "india" in location:
        if willing_to_relocate:
            return INDIA_OTHER_RELOCATE
        else:
            return INDIA_OTHER_NO_RELOCATE

    # Outside India
    if willing_to_relocate:
        return OUTSIDE_INDIA_RELOCATE
    else:
        return OUTSIDE_INDIA_NO_RELOCATE


# ============================================================================
# Dimension 6: Education (5%)
# ============================================================================

def score_education(candidate: dict) -> float:
    """
    Score education background.
    JD says skills > education, so this has lowest weight (5%).
    """
    education = candidate.get("education", [])

    if not education:
        return 0.3  # No education info = low but not zero

    best_score = 0.0

    for edu in education:
        score = 0.3  # Base

        # Institution tier
        tier = edu.get("tier", "unknown")
        tier_bonus = {
            "tier_1": 0.30,
            "tier_2": 0.20,
            "tier_3": 0.10,
            "tier_4": 0.0,
            "unknown": 0.05,
        }
        score += tier_bonus.get(tier, 0)

        # Field of study relevance
        field = edu.get("field_of_study", "").lower()
        relevant_fields = {
            "computer science": 0.25,
            "artificial intelligence": 0.30,
            "machine learning": 0.30,
            "data science": 0.25,
            "information technology": 0.15,
            "computer engineering": 0.20,
            "software engineering": 0.20,
            "electronics": 0.10,
            "electrical engineering": 0.10,
            "mathematics": 0.15,
            "statistics": 0.15,
            "physics": 0.08,
        }
        for f, bonus in relevant_fields.items():
            if f in field:
                score += bonus
                break

        # Degree level
        degree = edu.get("degree", "").lower()
        if "ph.d" in degree or "phd" in degree:
            score += 0.15
        elif "m.tech" in degree or "m.s." in degree or "m.e." in degree or "m.sc" in degree:
            score += 0.10
        elif "b.tech" in degree or "b.e." in degree or "b.sc" in degree:
            score += 0.05

        best_score = max(best_score, score)

    return min(1.0, best_score)


# ============================================================================
# Combined scorer
# ============================================================================

def compute_base_score(candidate: dict) -> tuple[float, dict]:
    """
    Compute the combined base score for a candidate across all dimensions.

    Returns:
        Tuple of (score, breakdown) where score is 0.0-1.0 and
        breakdown is a dict of dimension name → individual score.
    """
    breakdown = {
        "title_career": score_title_career(candidate),
        "skills_match": score_skills(candidate),
        "career_description": score_career_descriptions(candidate),
        "experience_fit": score_experience(candidate),
        "location": score_location(candidate),
        "education": score_education(candidate),
    }

    # Weighted sum — reads config.WEIGHTS live so slider changes take effect
    total = sum(
        breakdown[dim] * config.WEIGHTS[dim]
        for dim in breakdown
    )

    return total, breakdown
