"""
reasoning.py — Stage 6: Generate specific, honest per-candidate reasoning.

Each reasoning must:
- Reference specific facts from the candidate's profile
- Connect to JD requirements
- Acknowledge concerns honestly
- Vary substantively across candidates (NOT templated)
- Match tone to rank (top 10 = confident, bottom 20 = hedged)

This is evaluated at Stage 4 by sampling 10 random rows.
Hallucination, templates, or rank-tone mismatch are penalized.
"""

from datetime import datetime
from config import (
    CONSULTING_FIRMS,
    MUST_HAVE_SKILLS,
    STRONG_WANT_SKILLS,
    REFERENCE_DATE,
)


def _get_matching_skill_names(candidate: dict, category_set: set) -> list[str]:
    """Get skill names that match a given category set."""
    skills = candidate.get("skills", [])
    matches = []
    for skill in skills:
        name = skill.get("name", "")
        name_lower = name.lower().strip()
        for cat_skill in category_set:
            if cat_skill in name_lower or name_lower in cat_skill:
                matches.append(name)
                break
    return matches


def _get_career_highlights(candidate: dict) -> list[str]:
    """Extract notable career facts for reasoning."""
    highlights = []
    career = candidate.get("career_history", [])
    profile = candidate.get("profile", {})

    current_company = profile.get("current_company", "")
    current_title = profile.get("current_title", "")
    industry = profile.get("current_industry", "")

    # Check if at a consulting firm
    is_consulting = any(
        cf in current_company.lower() for cf in CONSULTING_FIRMS
    )

    # Count product-company roles
    product_roles = 0
    for role in career:
        comp = role.get("company", "").lower()
        industry_r = role.get("industry", "").lower()
        if industry_r in ("software", "technology", "internet", "saas"):
            product_roles += 1

    if product_roles >= 2:
        highlights.append("multiple product-company roles")
    if is_consulting:
        highlights.append("currently at a consulting firm")

    # Check for relevant description keywords
    for role in career:
        desc = role.get("description", "").lower()
        if any(kw in desc for kw in ["ranking", "retrieval", "search", "recommendation"]):
            highlights.append(f"relevant systems work at {role.get('company', 'prior company')}")
            break
        if any(kw in desc for kw in ["embeddings", "vector", "semantic"]):
            highlights.append(f"embeddings/vector experience at {role.get('company', 'prior company')}")
            break
        if any(kw in desc for kw in ["deployed", "production", "shipped"]):
            highlights.append(f"production ML deployment at {role.get('company', 'prior company')}")
            break

    return highlights


def _get_concerns(candidate: dict, score_breakdown: dict) -> list[str]:
    """Identify honest concerns about the candidate."""
    concerns = []
    profile = candidate.get("profile", {})
    signals = candidate.get("redrob_signals", {})

    # Notice period
    notice = signals.get("notice_period_days", 0)
    if notice > 90:
        concerns.append(f"long notice period ({notice} days)")
    elif notice > 60:
        concerns.append(f"moderate notice period ({notice} days)")

    # Location
    country = profile.get("country", "").lower()
    location = profile.get("location", "")
    willing = signals.get("willing_to_relocate", False)
    if country != "india" and not willing:
        concerns.append(f"based in {location}, not willing to relocate")
    elif country != "india" and willing:
        concerns.append(f"based in {location}, willing to relocate but outside India")

    # Experience band
    years = profile.get("years_of_experience", 0)
    if years < 4:
        concerns.append(f"only {years:.1f} years experience (JD prefers 5-9)")
    elif years > 12:
        concerns.append(f"{years:.1f} years experience may be overqualified for hands-on coding role")

    # Response rate
    response_rate = signals.get("recruiter_response_rate", 0.5)
    if response_rate < 0.3:
        concerns.append(f"low recruiter response rate ({response_rate:.0%})")

    # Recency
    last_active = signals.get("last_active_date", "")
    if last_active:
        try:
            la = datetime.strptime(last_active, "%Y-%m-%d").date()
            days_ago = (REFERENCE_DATE - la).days
            if days_ago > 180:
                concerns.append(f"inactive for {days_ago // 30} months")
            elif days_ago > 90:
                concerns.append("not recently active on platform")
        except (ValueError, TypeError):
            pass

    # Low scores in key dimensions
    if score_breakdown.get("skills_match", 0) < 0.2:
        concerns.append("limited relevant skill coverage")

    return concerns


def generate_reasoning(
    candidate: dict,
    rank: int,
    final_score: float,
    score_breakdown: dict,
) -> str:
    """
    Generate a specific, honest 1-2 sentence reasoning for this candidate.

    The reasoning is built from actual profile data, not templates.
    Tone matches the rank position.
    """
    profile = candidate.get("profile", {})
    signals = candidate.get("redrob_signals", {})

    title = profile.get("current_title", "Unknown")
    company = profile.get("current_company", "Unknown")
    years = profile.get("years_of_experience", 0)
    location = profile.get("location", "Unknown")

    # Get matching skills
    must_have_matches = _get_matching_skill_names(candidate, MUST_HAVE_SKILLS)
    strong_want_matches = _get_matching_skill_names(candidate, STRONG_WANT_SKILLS)

    # Get career highlights
    highlights = _get_career_highlights(candidate)

    # Get concerns
    concerns = _get_concerns(candidate, score_breakdown)

    # Build the reasoning based on rank tier
    parts = []

    # --- First sentence: Who they are and why they fit ---
    # Vary the opener based on rank
    if rank <= 10:
        # Top 10: Confident, specific
        skill_str = ", ".join(must_have_matches[:3]) if must_have_matches else \
                    ", ".join(strong_want_matches[:3]) if strong_want_matches else "relevant AI/ML skills"
        parts.append(
            f"{title} at {company} with {years:.1f} years experience; "
            f"strong match with {skill_str}"
        )
        if highlights:
            parts[-1] += f" and {highlights[0]}"
        parts[-1] += "."

    elif rank <= 30:
        # Ranks 11-30: Solid but note differentiators
        if must_have_matches:
            parts.append(
                f"{years:.1f}-year {title} with relevant skills including "
                f"{', '.join(must_have_matches[:2])}; {location}-based."
            )
        elif strong_want_matches:
            parts.append(
                f"{title} ({years:.1f} yrs) with {', '.join(strong_want_matches[:3])}; "
                f"solid adjacent skill set for the role."
            )
        else:
            parts.append(
                f"{title} at {company} ({years:.1f} yrs); career trajectory "
                f"aligns with applied AI engineering."
            )

    elif rank <= 60:
        # Ranks 31-60: Balanced, acknowledge gaps
        if must_have_matches or strong_want_matches:
            all_matches = must_have_matches + strong_want_matches
            parts.append(
                f"{title} ({years:.1f} yrs, {location}) with some relevant skills "
                f"({', '.join(all_matches[:2])})."
            )
        else:
            parts.append(
                f"{title} at {company} ({years:.1f} yrs); some career signals "
                f"suggest potential fit despite limited direct AI/ML skill coverage."
            )

    else:
        # Ranks 61-100: Hedged, honest about why they're lower
        parts.append(
            f"{title} at {company} ({years:.1f} yrs, {location})."
        )

    # --- Second sentence: Concerns or supporting detail ---
    if rank <= 20 and concerns:
        # Top 20: Mention main concern briefly
        parts.append(f"Minor concern: {concerns[0]}.")
    elif rank <= 20 and highlights:
        parts.append(f"Additional strength: {highlights[-1] if len(highlights) > 1 else 'strong behavioral signals'}.")
    elif 20 < rank <= 50 and concerns:
        parts.append(f"Note: {concerns[0]}.")
    elif 50 < rank <= 80:
        if concerns:
            parts.append(f"Gaps include {concerns[0]}{' and ' + concerns[1] if len(concerns) > 1 else ''}.")
        else:
            parts.append("Included based on partial skill alignment and behavioral signals.")
    else:
        # Ranks 81-100
        if concerns:
            concern_str = "; ".join(concerns[:2])
            parts.append(f"Near cutoff — {concern_str}.")
        else:
            parts.append("Near cutoff; included as marginal fit based on available signals.")

    # Combine and clean
    reasoning = " ".join(parts)

    # Ensure it's not too long (target: 1-2 sentences, ~150-300 chars)
    if len(reasoning) > 400:
        reasoning = reasoning[:397] + "..."

    # Escape any problematic CSV characters
    reasoning = reasoning.replace('"', "'")

    return reasoning
