import streamlit as st
import pandas as pd
import json
import gzip
import os
import yaml
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path

# Set Page Config for beautiful wide layout
st.set_page_config(
    page_title="Redrob AI Candidate Ranker Sandbox",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom premium styling using CSS injections
st.markdown("""
<style>
    /* Dark glassmorphic accent header */
    .header-container {
        background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
        padding: 2.5rem;
        border-radius: 12px;
        color: white;
        margin-bottom: 2rem;
        box-shadow: 0 4px 20px rgba(0,0,0,0.1);
    }
    .header-title {
        font-family: 'Outfit', 'Inter', sans-serif;
        font-size: 2.8rem;
        font-weight: 800;
        margin: 0;
        letter-spacing: -0.5px;
    }
    .header-subtitle {
        font-size: 1.1rem;
        opacity: 0.9;
        margin-top: 0.5rem;
    }
    
    /* Premium card containers */
    .metric-card {
        background-color: #ffffff;
        border: 1px solid #eef2f6;
        border-radius: 10px;
        padding: 1.5rem;
        box-shadow: 0 4px 6px rgba(0,0,0,0.02);
        transition: transform 0.2s ease;
    }
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(0,0,0,0.05);
    }
    
    /* Badges */
    .badge {
        display: inline-block;
        padding: 0.25rem 0.6rem;
        font-size: 0.8rem;
        font-weight: 600;
        border-radius: 4px;
        margin-right: 0.5rem;
    }
    .badge-must { background-color: #e8f5e9; color: #2e7d32; border: 1px solid #c8e6c9; }
    .badge-want { background-color: #e3f2fd; color: #1565c0; border: 1px solid #bbdefb; }
    .badge-nice { background-color: #fff3e0; color: #ef6c00; border: 1px solid #ffe0b2; }
    .badge-none { background-color: #eceff1; color: #37474f; border: 1px solid #cfd8dc; }
</style>
""", unsafe_allow_html=True)

# Import backend modules
import config
from loader import load_candidates
from prefilter import prefilter
from honeypot import detect_honeypots
from scorer import compute_base_score
from behavioral import compute_behavioral_modifier
from reasoning import generate_reasoning
from ranker import rank_candidates

# Default config weights
DEFAULT_WEIGHTS = {
    "title_career": 0.30,
    "skills_match": 0.25,
    "career_description": 0.15,
    "experience_fit": 0.15,
    "location": 0.10,
    "education": 0.05,
}

# Initialize session state for slider values on first run
for key, val in DEFAULT_WEIGHTS.items():
    if f"w_{key}" not in st.session_state:
        st.session_state[f"w_{key}"] = val

# Header Banner
st.markdown("""
<div class="header-container">
    <div class="header-title">🔍 Redrob AI Candidate Ranker Sandbox</div>
    <div class="header-subtitle">Intelligent Candidate Discovery & Ranking Engine — Interactive Exploration Sandbox</div>
</div>
""", unsafe_allow_html=True)

# Sidebar - Settings & File Upload
st.sidebar.header("⚙️ Pipeline Configuration")

# 1. Data Source Selection
data_source = st.sidebar.radio(
    "Select Candidate Dataset:",
    ["Sample Candidates (50)", "Upload Custom Dataset"]
)

candidates_data = []
dataset_name = ""

if data_source == "Sample Candidates (50)":
    sample_path = Path("sample_candidates.json")
    if sample_path.exists():
        try:
            with open(sample_path, "r", encoding="utf-8") as f:
                candidates_data = json.load(f)
            dataset_name = "sample_candidates.json"
        except Exception as e:
            st.sidebar.error(f"Error loading sample: {e}")
    else:
        st.sidebar.error("sample_candidates.json not found in work directory.")
else:
    uploaded_file = st.sidebar.file_uploader(
        "Upload JSON or JSONL (optionally .gz)",
        type=["json", "jsonl", "gz"]
)
    if uploaded_file is not None:
        try:
            # Handle gzipped files
            if uploaded_file.name.endswith(".gz"):
                with gzip.open(uploaded_file, "rt", encoding="utf-8") as f:
                    if uploaded_file.name.replace(".gz", "").endswith(".json"):
                        candidates_data = json.load(f)
                    else:  # Assume JSONL
                        candidates_data = [json.loads(line) for line in f if line.strip()]
            # Handle standard json/jsonl
            else:
                content = uploaded_file.read().decode("utf-8")
                if uploaded_file.name.endswith(".json"):
                    candidates_data = json.loads(content)
                else:  # jsonl
                    candidates_data = [json.loads(line) for line in content.splitlines() if line.strip()]
            dataset_name = uploaded_file.name
        except Exception as e:
            st.sidebar.error(f"Error loading uploaded file: {e}")

# If we have no data, stop
if not candidates_data:
    st.info("👋 Please upload a candidate dataset or select the sample candidates to begin.")
    st.stop()

# 2. Pipeline Stage Toggles
st.sidebar.subheader("Filter & Honeypot Options")
enable_prefilter = st.sidebar.checkbox("Enable Stage 1 Pre-filter", value=True)
enable_honeypots = st.sidebar.checkbox("Filter out Honeypots (Traps)", value=True)

# 3. Dynamic Weight Tuning
st.sidebar.subheader("Scoring Weight Tuning")
st.sidebar.markdown("<small>Adjust sliders below. Weights are auto-normalized to sum to 100%.</small>", unsafe_allow_html=True)

# Reset button must update session_state BEFORE sliders render
if st.sidebar.button("↺ Reset Weights to Default"):
    for key, val in DEFAULT_WEIGHTS.items():
        st.session_state[f"w_{key}"] = val

# Sliders use session_state as their value source (key= binds them two-way)
w_title = st.sidebar.slider("Title & Career Trajectory", 0.0, 1.0, step=0.05, key="w_title_career")
w_skills = st.sidebar.slider("Skills Alignment",          0.0, 1.0, step=0.05, key="w_skills_match")
w_desc   = st.sidebar.slider("Career Description Analysis",0.0, 1.0, step=0.05, key="w_career_description")
w_exp    = st.sidebar.slider("Experience Band Fit",        0.0, 1.0, step=0.05, key="w_experience_fit")
w_loc    = st.sidebar.slider("Location Proximity",         0.0, 1.0, step=0.05, key="w_location")
w_edu    = st.sidebar.slider("Education Background",       0.0, 1.0, step=0.05, key="w_education")

# Show live normalized percentages
sum_w = w_title + w_skills + w_desc + w_exp + w_loc + w_edu
if sum_w == 0:
    sum_w = 1.0
w_title_n = w_title / sum_w
w_skills_n = w_skills / sum_w
w_desc_n   = w_desc   / sum_w
w_exp_n    = w_exp    / sum_w
w_loc_n    = w_loc    / sum_w
w_edu_n    = w_edu    / sum_w

st.sidebar.caption(
    f"Normalized: Title {w_title_n:.0%} · Skills {w_skills_n:.0%} · Desc {w_desc_n:.0%} · "
    f"Exp {w_exp_n:.0%} · Loc {w_loc_n:.0%} · Edu {w_edu_n:.0%}"
)

# Apply to global config — use .update() NOT reassignment
# scorer.py holds a reference to this same dict object;
# reassigning would create a new dict scorer.py never sees.
config.WEIGHTS.update({
    "title_career":      w_title_n,
    "skills_match":      w_skills_n,
    "career_description": w_desc_n,
    "experience_fit":    w_exp_n,
    "location":          w_loc_n,
    "education":         w_edu_n,
})

# Run Pipeline
# NOTE: We do NOT use @st.cache_data here because:
# (a) candidates is a list-of-dicts which is unhashable in stlite
# (b) we WANT re-scoring when weights change
def run_pipeline(candidates, enable_pre, enable_hp, weights_tuple):
    # Apply weights to config — mutate in place so scorer.py sees the update
    config.WEIGHTS.update({
        "title_career":      weights_tuple[0],
        "skills_match":      weights_tuple[1],
        "career_description": weights_tuple[2],
        "experience_fit":    weights_tuple[3],
        "location":          weights_tuple[4],
        "education":         weights_tuple[5],
    })
    
    # 1. Pre-filter
    if enable_pre:
        filtered = prefilter(candidates)
        prefiltered_count = len(candidates) - len(filtered)
    else:
        filtered = candidates
        prefiltered_count = 0

    # 2. Honeypot detection
    honeypot_flags = detect_honeypots(filtered)
    honeypot_count = len(honeypot_flags)

    # 3. Score all filtered candidates
    scored_candidates = []
    excluded_candidates = []

    for candidate in filtered:
        cid = candidate.get("candidate_id", "")

        # Skip honeypots if enabled
        if enable_hp and cid in honeypot_flags:
            excluded_candidates.append(candidate)
            continue

        base_score, breakdown = compute_base_score(candidate)
        behavioral_mod, beh_breakdown = compute_behavioral_modifier(candidate)
        final_score = base_score * behavioral_mod

        scored_candidates.append({
            "candidate": candidate,
            "candidate_id": cid,
            "name": candidate.get("profile", {}).get("anonymized_name", "Anonymized"),
            "current_title": candidate.get("profile", {}).get("current_title", "N/A"),
            "current_company": candidate.get("profile", {}).get("current_company", "N/A"),
            "years_exp": candidate.get("profile", {}).get("years_of_experience", 0),
            "location": f"{candidate.get('profile', {}).get('location', 'N/A')}, {candidate.get('profile', {}).get('country', 'N/A')}",
            "base_score": base_score,
            "behavioral_mod": behavioral_mod,
            "final_score": final_score,
            "score_breakdown": breakdown,
            "behavioral_breakdown": beh_breakdown,
        })

    # Sort
    scored_candidates.sort(key=lambda x: (-x["final_score"], x["candidate_id"]))
    
    # Take top 100 (or all if less than 100)
    top_n = scored_candidates[:100]
    
    # Apply tie-breaking and non-increasing scores exactly like ranker.py
    for i, r in enumerate(top_n):
        r["rank"] = i + 1
        
    for i in range(1, len(top_n)):
        if top_n[i]["final_score"] >= top_n[i-1]["final_score"]:
            top_n[i]["final_score"] = top_n[i-1]["final_score"] - 0.000001
            
    # Generate reasoning for top_n
    for entry in top_n:
        entry["reasoning"] = generate_reasoning(
            candidate=entry["candidate"],
            rank=entry["rank"],
            final_score=entry["final_score"],
            score_breakdown=entry["score_breakdown"],
        )
        
    return top_n, len(candidates), prefiltered_count, honeypot_count, scored_candidates

weights_tuple = (w_title_n, w_skills_n, w_desc_n, w_exp_n, w_loc_n, w_edu_n)
top_results, total_count, prefiltered_count, honeypot_count, all_scored = run_pipeline(
    candidates_data, enable_prefilter, enable_honeypots, weights_tuple
)

# Statistics Dashboard Cards
c1, c2, c3, c4 = st.columns(4)
with c1:
    st.markdown(f"""
    <div class="metric-card">
        <div style="font-size: 0.9rem; color: #64748b; font-weight: 600;">DATASET LOADED</div>
        <div style="font-size: 1.8rem; font-weight: 700; color: #1e293b; margin-top: 0.5rem;">{total_count:,}</div>
        <div style="font-size: 0.8rem; color: #94a3b8; margin-top: 0.2rem;">{dataset_name}</div>
    </div>
    """, unsafe_allow_html=True)
with c2:
    st.markdown(f"""
    <div class="metric-card">
        <div style="font-size: 0.9rem; color: #64748b; font-weight: 600;">PRE-FILTER ELIMINATED</div>
        <div style="font-size: 1.8rem; font-weight: 700; color: #ef4444; margin-top: 0.5rem;">{prefiltered_count:,}</div>
        <div style="font-size: 0.8rem; color: #94a3b8; margin-top: 0.2rem;">{"" if not enable_prefilter else "Stage 1 active"}</div>
    </div>
    """, unsafe_allow_html=True)
with c3:
    st.markdown(f"""
    <div class="metric-card">
        <div style="font-size: 0.9rem; color: #64748b; font-weight: 600;">HONEYPOTS EXCLUDED</div>
        <div style="font-size: 1.8rem; font-weight: 700; color: #f59e0b; margin-top: 0.5rem;">{honeypot_count:,}</div>
        <div style="font-size: 0.8rem; color: #94a3b8; margin-top: 0.2rem;">{"Exclusion active" if enable_honeypots else "Exclusion disabled"}</div>
    </div>
    """, unsafe_allow_html=True)
with c4:
    avg_score = sum(x['final_score'] for x in top_results) / len(top_results) if top_results else 0.0
    st.markdown(f"""
    <div class="metric-card">
        <div style="font-size: 0.9rem; color: #64748b; font-weight: 600;">AVG SCORE (TOP 100)</div>
        <div style="font-size: 1.8rem; font-weight: 700; color: #10b981; margin-top: 0.5rem;">{avg_score:.4f}</div>
        <div style="font-size: 0.8rem; color: #94a3b8; margin-top: 0.2rem;">Final weighted score</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# Tabs
tab_lead, tab_inspect, tab_analytics, tab_meta = st.tabs([
    "🏆 Leaderboard", 
    "👤 Candidate Inspector", 
    "📈 Analytics & Distributions", 
    "📄 Submission Metadata"
])

# ==========================================
# TAB 1: LEADERBOARD
# ==========================================
with tab_lead:
    st.subheader("Top Ranked Candidates")
    
    if not top_results:
        st.warning("No candidates scored.")
    else:
        # Create dataframe for leaderboard table
        lead_df = pd.DataFrame([
            {
                "Rank": r["rank"],
                "ID": r["candidate_id"],
                "Name": r["name"],
                "Title": r["current_title"],
                "Company": r["current_company"],
                "Experience (Yrs)": r["years_exp"],
                "Location": r["location"],
                "Base Score": round(r["base_score"], 4),
                "Behavioral Mod": round(r["behavioral_mod"], 2),
                "Final Score": round(r["final_score"], 6)
            }
            for r in top_results
        ])
        
        st.dataframe(
            lead_df,
            column_config={
                "Rank": st.column_config.NumberColumn(width=60),
                "ID": st.column_config.TextColumn(width=120),
                "Final Score": st.column_config.NumberColumn(format="%.6f"),
            },
            hide_index=True,
            use_container_width=True
        )

        # Download submission CSV button
        csv_content = pd.DataFrame([
            {
                "candidate_id": r["candidate_id"],
                "rank": r["rank"],
                "score": f"{r['final_score']:.6f}",
                "reasoning": r["reasoning"]
            }
            for r in top_results
        ]).to_csv(index=False)

        st.download_button(
            label="📥 Download submission.csv",
            data=csv_content,
            file_name="submission.csv",
            mime="text/csv"
        )

# ==========================================
# TAB 2: CANDIDATE INSPECTOR
# ==========================================
with tab_inspect:
    st.subheader("Deep Candidate Profiler")
    
    if not top_results:
        st.warning("No candidates available for inspection.")
    else:
        # Candidate selection
        cand_options = {f"Rank {r['rank']}: {r['name']} ({r['candidate_id']})": r for r in top_results}
        selected_key = st.selectbox("Select Candidate to Inspect:", list(cand_options.keys()))
        
        if selected_key:
            entry = cand_options[selected_key]
            cand = entry["candidate"]
            profile = cand.get("profile", {})
            
            col_left, col_right = st.columns([1, 1])
            
            with col_left:
                st.markdown(f"### {profile.get('anonymized_name', 'Anonymized Candidate')} ({entry['candidate_id']})")
                st.markdown(f"**Headline**: {profile.get('headline', 'N/A')}")
                st.markdown(f"**Current Role**: {profile.get('current_title', 'N/A')} at **{profile.get('current_company', 'N/A')}** ({profile.get('current_company_size', 'N/A')} employees)")
                st.markdown(f"**Experience**: {profile.get('years_of_experience', 0)} years | **Location**: {profile.get('location', 'N/A')}, {profile.get('country', 'N/A')}")
                st.markdown(f"**Summary**:")
                st.info(profile.get("summary", "No summary provided."))
                
                # Reasoning
                st.markdown("#### 💡 Auto-Generated Reasoning")
                st.success(entry["reasoning"])
                
                # Education
                st.markdown("#### 🎓 Education History")
                for edu in cand.get("education", []):
                    grade_str = f" | Grade: {edu.get('grade')}" if edu.get('grade') else ""
                    st.markdown(f"- **{edu.get('degree', 'Degree')} in {edu.get('field_of_study', 'Field')}**  \n  {edu.get('institution', 'Institution')} ({edu.get('start_year', 'N/A')} - {edu.get('end_year', 'N/A')}) | {edu.get('tier', 'unknown').upper()}{grade_str}")
                    
                # Career history
                st.markdown("#### 💼 Work History Timeline")
                for job in cand.get("career_history", []):
                    current_badge = " [CURRENT]" if job.get("is_current") else ""
                    st.markdown(f"- **{job.get('title')}** at {job.get('company')}{current_badge}  \n  *{job.get('start_date')} to {job.get('end_date') or 'Present'} ({job.get('duration_months', 0)} months)*  \n  {job.get('description', '')}")
            
            with col_right:
                st.markdown("### 📊 Scoring Breakdown")
                
                # Plot Base Score Breakdown
                breakdown = entry["score_breakdown"]
                w_labels = {
                    "title_career": "Title & Career Trajectory",
                    "skills_match": "Skills Match",
                    "career_description": "Career Description",
                    "experience_fit": "Experience Fit",
                    "location": "Location Proximity",
                    "education": "Education"
                }
                
                score_data = pd.DataFrame([
                    {
                        "Dimension": w_labels[k],
                        "Raw Score": round(v, 4),
                        "Weight": round(config.WEIGHTS[k], 4),
                        "Weighted Contribution": round(v * config.WEIGHTS[k], 4)
                    }
                    for k, v in breakdown.items()
                ])
                
                # Multiplier visualization
                st.metric(
                    label="Final Combined Score (Base × Behavioral Modifier)",
                    value=f"{entry['final_score']:.6f}",
                    delta=f"Base: {entry['base_score']:.4f} | Mod: x{entry['behavioral_mod']:.2f}"
                )
                
                fig_base = px.bar(
                    score_data,
                    x="Dimension",
                    y=["Weighted Contribution", "Raw Score"],
                    barmode="group",
                    title="Base Score Component Contributions & Raw Scores",
                    color_discrete_sequence=["#1f77b4", "#aec7e8"]
                )
                fig_base.update_layout(yaxis_range=[0, 1])
                st.plotly_chart(fig_base, use_container_width=True)
                
                # Behavioral Modifiers
                st.markdown("#### ⚡ Behavioral Signals Breakdown")
                beh_breakdown = entry["behavioral_breakdown"]
                
                beh_df = pd.DataFrame([
                    {"Signal": k.replace("_", " ").title(), "Multiplier": round(v, 3)}
                    for k, v in beh_breakdown.items()
                ])
                
                # Highlight impact (e.g. green for >1.0, red for <1.0)
                fig_beh = px.bar(
                    beh_df,
                    y="Signal",
                    x="Multiplier",
                    orientation="h",
                    title="Behavioral Multipliers Impact (Neutral is 1.0)",
                    color="Multiplier",
                    color_continuous_scale=px.colors.diverging.RdYlGn,
                    color_continuous_midpoint=1.0
                )
                st.plotly_chart(fig_beh, use_container_width=True)
                
                # Skills matching badge list
                st.markdown("#### 🛠️ Skills Matching Profile")
                skills_list = cand.get("skills", [])
                
                # Classify skills using backend categories
                from config import MUST_HAVE_SKILLS, STRONG_WANT_SKILLS, NICE_TO_HAVE_SKILLS, NON_TECH_SKILLS
                
                must_have = []
                strong_want = []
                nice_to_have = []
                other_tech = []
                non_tech = []
                
                for s in skills_list:
                    name = s.get("name", "").lower().strip()
                    prof = s.get("proficiency", "unknown")
                    dur = s.get("duration_months", 0)
                    endors = s.get("endorsements", 0)
                    display_text = f"{s.get('name')} ({prof}, {dur}m, 👍{endors})"
                    
                    if name in MUST_HAVE_SKILLS:
                        must_have.append(display_text)
                    elif name in STRONG_WANT_SKILLS:
                        strong_want.append(display_text)
                    elif name in NICE_TO_HAVE_SKILLS:
                        nice_to_have.append(display_text)
                    elif name in NON_TECH_SKILLS:
                        non_tech.append(display_text)
                    else:
                        other_tech.append(display_text)
                
                if must_have:
                    st.markdown("**Must-Have Skills:**")
                    for s in must_have:
                        st.markdown(f'<span class="badge badge-must">{s}</span>', unsafe_allow_html=True)
                if strong_want:
                    st.markdown("**Strong-Want Skills:**")
                    for s in strong_want:
                        st.markdown(f'<span class="badge badge-want">{s}</span>', unsafe_allow_html=True)
                if nice_to_have:
                    st.markdown("**Nice-To-Have Skills:**")
                    for s in nice_to_have:
                        st.markdown(f'<span class="badge badge-nice">{s}</span>', unsafe_allow_html=True)
                if other_tech:
                    st.markdown("**Other Tech Skills:**")
                    for s in other_tech:
                        st.markdown(f'<span class="badge badge-nice">{s}</span>', unsafe_allow_html=True)
                if non_tech:
                    st.markdown("**Non-Tech / Soft Skills:**")
                    for s in non_tech:
                        st.markdown(f'<span class="badge badge-none">{s}</span>', unsafe_allow_html=True)

# ==========================================
# TAB 3: ANALYTICS & DISTRIBUTIONS
# ==========================================
with tab_analytics:
    st.subheader("Dataset Demographics & Distributions")
    
    if not all_scored:
        st.warning("No data scored.")
    else:
        # Prepare scoring dataframe
        scored_df = pd.DataFrame([
            {
                "candidate_id": r["candidate_id"],
                "years_exp": r["years_exp"],
                "base_score": r["base_score"],
                "behavioral_mod": r["behavioral_mod"],
                "final_score": r["final_score"],
                "location": r["location"]
            }
            for r in all_scored
        ])
        
        col_an1, col_an2 = st.columns(2)
        
        with col_an1:
            # Score distribution
            fig_dist = px.histogram(
                scored_df, 
                x="final_score", 
                nbins=30,
                title="Candidate Final Score Distribution",
                color_discrete_sequence=["#2a5298"]
            )
            st.plotly_chart(fig_dist, use_container_width=True)
            
            # Scatter plot: Base Score vs Behavioral Mod
            fig_scatter = px.scatter(
                scored_df,
                x="base_score",
                y="behavioral_mod",
                color="final_score",
                hover_data=["candidate_id"],
                title="Base Score vs. Behavioral Modifier",
                color_continuous_scale="Viridis"
            )
            st.plotly_chart(fig_scatter, use_container_width=True)
            
        with col_an2:
            # Experience distribution
            fig_exp = px.histogram(
                scored_df,
                x="years_exp",
                nbins=20,
                title="Years of Experience Distribution",
                color_discrete_sequence=["#10b981"]
            )
            st.plotly_chart(fig_exp, use_container_width=True)
            
            # Top Locations
            top_locs = scored_df["location"].value_counts().reset_index()
            top_locs.columns = ["Location", "Count"]
            fig_loc = px.bar(
                top_locs.head(10),
                x="Count",
                y="Location",
                orientation="h",
                title="Top 10 Candidate Locations",
                color_discrete_sequence=["#8b5cf6"]
            )
            st.plotly_chart(fig_loc, use_container_width=True)

# ==========================================
# TAB 4: SUBMISSION METADATA
# ==========================================
with tab_meta:
    st.subheader("Submission Metadata configuration (`submission_metadata.yaml`)")
    
    meta_path = Path("submission_metadata.yaml")
    
    # Check if file exists, if not write initial template
    if not meta_path.exists():
        default_meta = {
            "team_name": "Kalpit Phogat",
            "primary_contact": {
                "name": "Kalpit Phogat",
                "email": "kalpitphogat@gmail.com",
                "phone": "+91-XXXXXXXXXX"
            },
            "team_members": [
                {
                    "name": "Kalpit Phogat",
                    "email": "kalpitphogat@gmail.com",
                    "role": "ML Engineer"
                }
            ],
            "github_repo": "https://github.com/kalpitphogat/redrob_AI",
            "sandbox_link": "https://redrob-ai.streamlit.app",
            "reproduce_command": "python rank.py --candidates ./candidates.jsonl --out ./submission.csv",
            "compute": {
                "platform": "Windows 11 PC",
                "cpu_cores": 12,
                "ram_gb": 16,
                "python_version": "3.11.4",
                "os": "Windows 11",
                "uses_gpu_for_inference": False,
                "has_network_during_ranking": False,
                "pre_computation_required": False,
                "pre_computation_time_minutes": 0
            },

            "methodology_summary": "Standard python implementation of multi-stage Candidate discovery. Consists of fast pre-filtering (Stage 1), honeypot extraction, title relevance mapping, semantic trust weighting on skills, and behavioral modifications.",
            "declarations": {
                "read_submission_spec": True,
                "code_is_original_work": True,
                "no_collusion": True,
                "honeypot_check_done": True,
                "reproduction_tested": True
            }
        }
        
        try:
            with open(meta_path, "w", encoding="utf-8") as f:
                yaml.dump(default_meta, f, default_flow_style=False, sort_keys=False)
        except Exception as e:
            st.error(f"Error writing metadata file: {e}")

    # Read and allow editing/viewing
    if meta_path.exists():
        try:
            with open(meta_path, "r", encoding="utf-8") as f:
                meta_content = f.read()
                
            st.markdown("You can edit the `submission_metadata.yaml` file directly below, then click **Save Changes** to write to the file.")
            
            edited_meta = st.text_area(
                label="submission_metadata.yaml contents",
                value=meta_content,
                height=400
            )
            
            if st.button("Save Changes"):
                try:
                    # Validate YAML syntax
                    yaml.safe_load(edited_meta)
                    with open(meta_path, "w", encoding="utf-8") as f:
                        f.write(edited_meta)
                    st.success("Successfully updated submission_metadata.yaml! ✅")
                    st.rerun()
                except Exception as ex:
                    st.error(f"Invalid YAML syntax: {ex}")
                    
            st.download_button(
                label="📥 Download submission_metadata.yaml",
                data=edited_meta,
                file_name="submission_metadata.yaml",
                mime="text/yaml"
            )
        except Exception as e:
            st.error(f"Error reading metadata: {e}")
