"""
honeypot.py — Stage 3: Honeypot candidate detection.

Identifies ~80 candidates with subtly impossible profiles.
Submissions with >10% honeypots in top 100 are DISQUALIFIED.

Detection signals:
1. Salary min > max
2. Expert proficiency in many skills with 0 or tiny duration
3. Skill assessment score contradicts claimed proficiency
4. Impossible date arithmetic
5. Massive skill count with all expert/advanced but no career backing
"""

from datetime import datetime
from config import (
    HONEYPOT_EXPERT_SKILL_COUNT,
    HONEYPOT_MIN_DURATION_FOR_EXPERT,
    HONEYPOT_ZERO_DURATION_EXPERT,
    HONEYPOT_ASSESSMENT_FAIL_THRESHOLD,
)


def _check_salary_inversion(candidate: dict) -> bool:
    """Check if salary min > max (impossible)."""
    signals = candidate.get("redrob_signals", {})
    salary = signals.get("expected_salary_range_inr_lpa", {})
    sal_min = salary.get("min", 0)
    sal_max = salary.get("max", 0)

    if sal_min > 0 and sal_max > 0 and sal_min > sal_max:
        return True
    return False


def _check_expert_skill_inflation(candidate: dict) -> tuple[bool, int]:
    """
    Check for suspicious expert/advanced skill claims:
    - Too many expert-level skills
    - Expert skills with 0 or very short duration
    """
    skills = candidate.get("skills", [])

    expert_advanced_count = 0
    zero_duration_expert = 0
    low_duration_expert = 0

    for skill in skills:
        prof = skill.get("proficiency", "").lower()
        duration = skill.get("duration_months", 0)

        if prof in ("expert", "advanced"):
            expert_advanced_count += 1
            if duration == 0:
                zero_duration_expert += 1
            elif duration < HONEYPOT_MIN_DURATION_FOR_EXPERT:
                low_duration_expert += 1

    # Flag 1: Too many expert/advanced skills with zero duration
    if zero_duration_expert >= HONEYPOT_ZERO_DURATION_EXPERT:
        return True, expert_advanced_count

    # Flag 2: Absurdly many expert-level skills
    if expert_advanced_count >= HONEYPOT_EXPERT_SKILL_COUNT and zero_duration_expert >= 2:
        return True, expert_advanced_count

    return False, expert_advanced_count


def _check_assessment_contradiction(candidate: dict) -> bool:
    """
    Check if skill assessment scores contradict claimed proficiency.
    E.g., claims 'expert' in Python but assessment score is 15.
    """
    signals = candidate.get("redrob_signals", {})
    assessment_scores = signals.get("skill_assessment_scores", {})
    skills = candidate.get("skills", [])

    if not assessment_scores:
        return False

    contradictions = 0
    for skill in skills:
        skill_name = skill.get("name", "")
        prof = skill.get("proficiency", "").lower()

        if skill_name in assessment_scores and prof in ("expert", "advanced"):
            score = assessment_scores[skill_name]
            if score < HONEYPOT_ASSESSMENT_FAIL_THRESHOLD:
                contradictions += 1

    # Multiple contradictions = suspicious
    return contradictions >= 2


def _check_impossible_dates(candidate: dict) -> bool:
    """
    Check for impossible date configurations:
    - Career start_date after end_date
    - Duration doesn't match date range (large discrepancy)
    - Dates in the far future
    """
    career = candidate.get("career_history", [])

    for role in career:
        start_str = role.get("start_date", "")
        end_str = role.get("end_date")
        duration = role.get("duration_months", 0)

        if not start_str:
            continue

        try:
            start = datetime.strptime(start_str, "%Y-%m-%d")

            if end_str:
                end = datetime.strptime(end_str, "%Y-%m-%d")

                # Start after end
                if start > end:
                    return True

                # Duration wildly inconsistent with dates
                actual_months = (end.year - start.year) * 12 + (end.month - start.month)
                if abs(actual_months - duration) > 12:
                    return True

        except (ValueError, TypeError):
            continue

    return False


def _check_title_skills_extreme_mismatch(candidate: dict) -> bool:
    """
    Check for extreme title-skills mismatch that suggests a honeypot:
    - Non-technical title (Marketing Manager, Accountant) with 10+ advanced AI skills
    - This is different from keyword stuffers (who are traps but not honeypots)
    """
    profile = candidate.get("profile", {})
    title = profile.get("current_title", "").lower()
    skills = candidate.get("skills", [])

    non_tech_titles = {
        "marketing manager", "hr manager", "accountant",
        "sales executive", "customer support", "content writer",
        "graphic designer", "operations manager",
    }

    if title not in non_tech_titles:
        return False

    # Count advanced/expert AI-specific skills
    ai_skill_keywords = {
        "nlp", "deep learning", "machine learning", "pytorch", "tensorflow",
        "transformers", "bert", "gpt", "llm", "rag", "embeddings",
        "fine-tuning", "lora", "qlora", "neural", "reinforcement learning",
    }

    expert_ai_count = 0
    for skill in skills:
        name = skill.get("name", "").lower()
        prof = skill.get("proficiency", "").lower()
        if prof in ("expert", "advanced"):
            for kw in ai_skill_keywords:
                if kw in name:
                    expert_ai_count += 1
                    break

    # Non-tech title with 5+ expert AI skills and all 0 endorsements
    # is suspicious even beyond normal keyword stuffing
    return expert_ai_count >= 5


def _check_signup_after_last_active(candidate: dict) -> bool:
    """Check if signup date is after last active date (impossible)."""
    signals = candidate.get("redrob_signals", {})
    signup = signals.get("signup_date", "")
    last_active = signals.get("last_active_date", "")

    if not signup or not last_active:
        return False

    try:
        s = datetime.strptime(signup, "%Y-%m-%d")
        la = datetime.strptime(last_active, "%Y-%m-%d")
        # Signup significantly after last active = suspicious
        if s > la and (s - la).days > 30:
            return True
    except (ValueError, TypeError):
        pass

    return False


def detect_honeypots(candidates: list[dict]) -> dict[str, list[str]]:
    """
    Scan all candidates for honeypot indicators.

    Returns:
        Dictionary mapping candidate_id to list of reasons they were flagged.
        Only candidates with at least one flag are included.
    """
    flagged = {}

    for candidate in candidates:
        cid = candidate.get("candidate_id", "")
        reasons = []

        # Check 1: Salary inversion
        if _check_salary_inversion(candidate):
            reasons.append("salary_min_gt_max")

        # Check 2: Expert skill inflation
        is_inflated, expert_count = _check_expert_skill_inflation(candidate)
        if is_inflated:
            reasons.append(f"expert_skill_inflation({expert_count}_expert_skills)")

        # Check 3: Assessment score contradictions
        if _check_assessment_contradiction(candidate):
            reasons.append("assessment_contradicts_proficiency")

        # Check 4: Impossible dates
        if _check_impossible_dates(candidate):
            reasons.append("impossible_dates")

        # Check 5: Extreme title-skills mismatch (beyond normal stuffing)
        if _check_title_skills_extreme_mismatch(candidate):
            reasons.append("extreme_title_skills_mismatch")

        # Check 6: Signup after last active
        if _check_signup_after_last_active(candidate):
            reasons.append("signup_after_last_active")

        # A candidate is flagged as honeypot if they have 2+ independent signals
        # OR one very strong signal (salary inversion, impossible dates)
        strong_signals = {"salary_min_gt_max", "impossible_dates"}
        has_strong = any(r in strong_signals for r in reasons)

        if len(reasons) >= 2 or has_strong:
            flagged[cid] = reasons

    print(f"Honeypot detection: flagged {len(flagged)} candidates")
    return flagged
