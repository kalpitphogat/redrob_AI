"""
behavioral.py — Stage 4: Behavioral signal modifier.

Applies a multiplicative modifier to the base score based on
the candidate's platform activity and engagement signals.

The JD explicitly states: "a perfect-on-paper candidate who hasn't
logged in for 6 months and has a 5% recruiter response rate is,
for hiring purposes, not actually available."
"""

from datetime import datetime, date
from config import (
    REFERENCE_DATE,
    ACTIVE_VERY_RECENT_DAYS,
    ACTIVE_RECENT_DAYS,
    ACTIVE_STALE_DAYS,
    RESPONSE_RATE_EXCELLENT,
    RESPONSE_RATE_GOOD,
    RESPONSE_RATE_POOR,
    RESPONSE_TIME_FAST,
    RESPONSE_TIME_OK,
    RESPONSE_TIME_SLOW,
    NOTICE_IDEAL,
    NOTICE_ACCEPTABLE,
    NOTICE_LONG,
    NOTICE_VERY_LONG,
)


def _recency_modifier(last_active_str: str) -> float:
    """
    Score based on how recently the candidate was active.
    JD says inactive candidates are effectively unavailable.
    """
    if not last_active_str:
        return 0.7

    try:
        last_active = datetime.strptime(last_active_str, "%Y-%m-%d").date()
        days_ago = (REFERENCE_DATE - last_active).days

        if days_ago < 0:
            # Active "in the future" — treat as very recent
            return 1.1
        elif days_ago <= ACTIVE_VERY_RECENT_DAYS:
            return 1.10
        elif days_ago <= ACTIVE_RECENT_DAYS:
            return 1.0
        elif days_ago <= ACTIVE_STALE_DAYS:
            return 0.80
        else:
            return 0.55  # Inactive 6+ months — significant penalty
    except (ValueError, TypeError):
        return 0.7


def _open_to_work_modifier(open_flag: bool) -> float:
    """Candidates marked as open to work are more likely to engage."""
    return 1.08 if open_flag else 0.90


def _response_rate_modifier(rate: float) -> float:
    """
    Based on recruiter_response_rate.
    Low response rate = candidate likely unresponsive.
    """
    if rate >= RESPONSE_RATE_EXCELLENT:
        return 1.12
    elif rate >= RESPONSE_RATE_GOOD:
        return 1.0
    elif rate >= RESPONSE_RATE_POOR:
        return 0.82
    else:
        return 0.60  # <20% response rate = almost unreachable


def _response_time_modifier(hours: float) -> float:
    """
    Based on avg_response_time_hours.
    Fast responders are more hirable.
    """
    if hours <= RESPONSE_TIME_FAST:
        return 1.08
    elif hours <= RESPONSE_TIME_OK:
        return 1.0
    elif hours <= RESPONSE_TIME_SLOW:
        return 0.90
    else:
        return 0.78


def _notice_period_modifier(days: int) -> float:
    """
    JD says: "sub-30-day notice ideal, can buy out up to 30 days,
    30+ day notice candidates still in scope but bar gets higher."
    """
    if days <= NOTICE_IDEAL:
        return 1.10
    elif days <= NOTICE_ACCEPTABLE:
        return 1.0
    elif days <= NOTICE_LONG:
        return 0.90
    elif days <= NOTICE_VERY_LONG:
        return 0.80
    else:
        return 0.70


def _interview_completion_modifier(rate: float) -> float:
    """
    Candidates who complete interviews are more serious.
    Low completion rate = flight risk / not serious.
    """
    if rate >= 0.8:
        return 1.05
    elif rate >= 0.5:
        return 0.95
    else:
        return 0.78


def _profile_completeness_modifier(score: float) -> float:
    """
    Higher profile completeness suggests a more engaged candidate.
    Low completeness = less invested in job search.
    """
    if score >= 80:
        return 1.05
    elif score >= 50:
        return 1.0
    elif score >= 30:
        return 0.92
    else:
        return 0.85


def _github_modifier(score: float) -> float:
    """
    GitHub activity is a positive signal for engineering roles.
    -1 means no GitHub linked (neutral, not penalty).
    """
    if score < 0:
        return 1.0  # No GitHub = neutral
    elif score >= 70:
        return 1.12
    elif score >= 40:
        return 1.06
    elif score >= 10:
        return 1.02
    else:
        return 1.0


def _verification_modifier(verified_email: bool, verified_phone: bool,
                           linkedin: bool) -> float:
    """
    Verified accounts are more trustworthy.
    Unverified on everything = slight concern.
    """
    mod = 1.0
    if verified_email and verified_phone:
        mod *= 1.03
    elif not verified_email and not verified_phone:
        mod *= 0.90

    if linkedin:
        mod *= 1.02

    return mod


def _work_mode_modifier(preferred_mode: str) -> float:
    """
    JD is hybrid (flexible cadence). Remote-only may be a mismatch.
    """
    mode = preferred_mode.lower() if preferred_mode else ""
    if mode in ("hybrid", "flexible"):
        return 1.02
    elif mode == "onsite":
        return 1.0
    elif mode == "remote":
        return 0.95
    else:
        return 1.0


def _saved_by_recruiters_modifier(count: int) -> float:
    """
    Being saved by recruiters indicates market desirability.
    """
    if count >= 10:
        return 1.06
    elif count >= 5:
        return 1.03
    elif count >= 1:
        return 1.0
    else:
        return 0.97


def compute_behavioral_modifier(candidate: dict) -> tuple[float, dict]:
    """
    Compute the multiplicative behavioral modifier for a candidate.

    The modifier adjusts the base content-match score up or down
    based on the candidate's platform engagement and availability signals.

    Returns:
        Tuple of (modifier, breakdown_dict) where modifier is clamped
        to [0.3, 1.3] and breakdown_dict shows each component.
    """
    signals = candidate.get("redrob_signals", {})

    components = {
        "recency": _recency_modifier(signals.get("last_active_date", "")),
        "open_to_work": _open_to_work_modifier(signals.get("open_to_work_flag", False)),
        "response_rate": _response_rate_modifier(signals.get("recruiter_response_rate", 0.5)),
        "response_time": _response_time_modifier(signals.get("avg_response_time_hours", 72)),
        "notice_period": _notice_period_modifier(signals.get("notice_period_days", 60)),
        "interview_completion": _interview_completion_modifier(
            signals.get("interview_completion_rate", 0.5)
        ),
        "profile_completeness": _profile_completeness_modifier(
            signals.get("profile_completeness_score", 50)
        ),
        "github": _github_modifier(signals.get("github_activity_score", -1)),
        "verification": _verification_modifier(
            signals.get("verified_email", False),
            signals.get("verified_phone", False),
            signals.get("linkedin_connected", False),
        ),
        "work_mode": _work_mode_modifier(signals.get("preferred_work_mode", "")),
        "recruiter_saves": _saved_by_recruiters_modifier(
            signals.get("saved_by_recruiters_30d", 0)
        ),
    }

    # Multiply all modifiers together
    modifier = 1.0
    for value in components.values():
        modifier *= value

    # Clamp to reasonable range
    modifier = max(0.3, min(1.3, modifier))

    return modifier, components
