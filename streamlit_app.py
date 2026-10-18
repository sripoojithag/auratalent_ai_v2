import os
import time
import pandas as pd
import streamlit as st

# Set page config
st.set_page_config(
    page_title="AuraTalent AI - Enterprise Candidate Matcher",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom premium styling
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    .main-header {
        background: linear-gradient(135deg, #1e1b4b 0%, #0f172a 100%);
        padding: 2.5rem;
        border-radius: 12px;
        color: white;
        margin-bottom: 2rem;
        border: 1px solid #312e81;
    }
    
    .telemetry-card {
        background-color: #0f172a;
        padding: 1.25rem;
        border-radius: 8px;
        border: 1px solid #1e293b;
        color: #f1f5f9;
        margin-bottom: 1rem;
    }
    
    .candidate-card {
        background-color: #1e293b;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 5px solid #6366f1;
        margin-bottom: 1.5rem;
    }
    
    .score-badge {
        background-color: #312e81;
        color: #e0e7ff;
        padding: 0.25rem 0.75rem;
        border-radius: 9999px;
        font-weight: 600;
        font-family: 'JetBrains Mono', monospace;
    }
    
    .timeline-item {
        border-left: 2px solid #475569;
        padding-left: 1.25rem;
        position: relative;
        margin-bottom: 1.25rem;
    }
    
    .timeline-item::before {
        content: '';
        position: absolute;
        width: 10px;
        height: 10px;
        border-radius: 50%;
        background-color: #6366f1;
        left: -6px;
        top: 6px;
    }
    
    .metric-value {
        font-family: 'JetBrains Mono', monospace;
        font-weight: 700;
        color: #818cf8;
    }
</style>
""", unsafe_allow_html=True)

from src.server.generator import generate_candidate_dataset
from src.server.pipeline import run_ranking_pipeline
import src.server.embedding_ranker as er
from src.server.reasoning import generate_gemini_explanation

DEFAULT_JOB_DESCRIPTION = """We are seeking a Senior Machine Learning Platform Engineer to design, build, and optimize high-throughput distributed LLM retrieval systems (RAG).

Required Skills:
- PyTorch, Python, and Transformers
- Vector Databases (Pinecone, Milvus, Qdrant)
- Docker, Kubernetes, and Ray

Preferred Skills:
- Experience with MLOps pipelines (MLflow, Kubeflow)
- Deep learning performance optimization (TensorRT, vLLM)
- Strong contributions to open-source ML frameworks

Experience Required:
- 5+ years of industry experience working with production-grade ML infrastructure.
"""

# Global Shared Candidate Pool Cache
@st.cache_resource
def load_cached_candidate_pool():
    # Warm up local embedding model
    er.init_embedding_model()
    # Generate 100,000 resumes
    candidates = generate_candidate_dataset(100000)
    # Trigger background FAISS indexing
    er.build_faiss_index_bg(candidates)
    return candidates

# Load pool
with st.spinner("Preparing 100,000 synthetic resume pool & warming models..."):
    candidates_pool = load_cached_candidate_pool()

# Sidebar Setup
st.sidebar.image("https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?auto=format&fit=crop&w=120&h=120&q=80", width=80)
st.sidebar.title("AuraTalent AI")
st.sidebar.caption("Enterprise Hybrid Ranking Engine")

st.sidebar.markdown("---")

# Model Settings
st.sidebar.subheader("System Configuration")
top_k = st.sidebar.slider("Stage 1 Filter Size (Top-K)", min_value=500, max_value=5000, value=2000, step=100)
use_gemini_embedding = st.sidebar.checkbox("Use Gemini Cloud Embeddings (text-embedding-004)", value=False)
if use_gemini_embedding and not os.environ.get("GEMINI_API_KEY"):
    st.sidebar.warning("⚠️ No GEMINI_API_KEY found. Will fall back to Local Embeddings.")

st.sidebar.markdown("---")

# Health Status Panel
st.sidebar.subheader("System Status")
status_col1, status_col2 = st.sidebar.columns(2)
with status_col1:
    st.metric("Pool Size", f"{len(candidates_pool):,}")
    st.metric("Embedder", "MiniLM" if not use_gemini_embedding else "Gemini")
with status_col2:
    st.metric("FAISS Status", er._faiss_status.split(" ")[0].title())
    st.metric("Model Status", er.get_model_status().title())

# Main Page Header
st.markdown("""
<div class="main-header">
    <h1 style='margin:0; font-size: 2.2rem; font-weight: 700; tracking: tight;'>AuraTalent AI</h1>
    <p style='margin:5px 0 0 0; color: #cbd5e1; font-size: 1.1rem;'>100,000 Resume Semantic Matching & Multi-Stage Scoring Pipeline</p>
</div>
""", unsafe_allow_html=True)

# Layout: Two columns for input setup
col_left, col_right = st.columns([3, 2])

with col_left:
    st.subheader("1. Job Description & Criteria")
    job_desc_input = st.text_area(
        "Paste Target Position Requirements",
        value=DEFAULT_JOB_DESCRIPTION,
        height=280
    )

with col_right:
    st.subheader("2. Hybrid Ranking Weights")
    st.caption("Adjust weight importance. Total must sum to 100%.")
    
    # Initialize slider values in session state
    if "sem_w" not in st.session_state:
        st.session_state.sem_w = 50
    if "skills_w" not in st.session_state:
        st.session_state.skills_w = 25
    if "career_w" not in st.session_state:
        st.session_state.career_w = 15
    if "beh_w" not in st.session_state:
        st.session_state.beh_w = 10

    # Sliders
    sem_w = st.slider("Semantic Alignment", 0, 100, key="sem_w_slider", value=st.session_state.sem_w)
    skills_w = st.slider("Technical Skill Matrix", 0, 100, key="skills_w_slider", value=st.session_state.skills_w)
    career_w = st.slider("Career Growth & Longevity", 0, 100, key="career_w_slider", value=st.session_state.career_w)
    beh_w = st.slider("Talent Behavioral Signals", 0, 100, key="beh_w_slider", value=st.session_state.beh_w)

    current_sum = sem_w + skills_w + career_w + beh_w
    
    if current_sum != 100:
        st.warning(f"⚠️ Sum of weights is currently **{current_sum}%**. We will automatically normalize them to 100% when running.")
        if st.button("Fix & Balance Weights Automatically"):
            # Normalize to 100
            total = max(1, current_sum)
            st.session_state.sem_w = int(round(sem_w / total * 100))
            st.session_state.skills_w = int(round(skills_w / total * 100))
            st.session_state.career_w = int(round(career_w / total * 100))
            st.session_state.beh_w = 100 - (st.session_state.sem_w + st.session_state.skills_w + st.session_state.career_w)
            st.rerun()
    else:
        st.success("✅ Weights sum to exactly 100%. Ready.")

# Run button
run_pipeline = st.button("🚀 Run Enterprise Matching Pipeline", type="primary", use_container_width=True)

if run_pipeline or "pipeline_results" in st.session_state:
    if run_pipeline:
        # Run matching pipeline
        norm_weights = {
            "semantic": sem_w / max(1, current_sum),
            "skills": skills_w / max(1, current_sum),
            "career": career_w / max(1, current_sum),
            "behavioral": beh_w / max(1, current_sum)
        }
        
        config = {
            "jobDescriptionText": job_desc_input,
            "topKRetrieval": top_k,
            "useGeminiEmbedding": use_gemini_embedding,
            "weights": norm_weights
        }
        
        with st.spinner("Executing 3-Stage Pipeline (Stage 1 Filtering -> Stage 2 Semantic Encoding -> Stage 3 Scoring)..."):
            results = run_ranking_pipeline(candidates_pool, config)
            st.session_state.pipeline_results = results
            # Clear previous selected candidate or AI explanations
            st.session_state.selected_candidate_id = None
            st.session_state.local_ai_explanations = {}
            st.success("Pipeline executed successfully!")

    results = st.session_state.pipeline_results
    telemetry = results["telemetry"]
    top_candidates = results["topCandidates"]
    parsed = results["parsedFeatures"]

    # Show telemetry metrics
    st.markdown("---")
    st.subheader("3. Match Results & Execution Analytics")
    
    tel_col1, tel_col2, tel_col3, tel_col4, tel_col5 = st.columns(5)
    with tel_col1:
        st.metric("Candidates Searched", f"{telemetry['totalCandidates']:,}")
    with tel_col2:
        st.metric("Stage 1 Retrieved", f"{telemetry['stage1CandidatesCount']:,}")
    with tel_col3:
        st.metric("Stage 1 Speed", f"{telemetry['stage1TimeMs']} ms")
    with tel_col4:
        st.metric("Stage 2 Speed", f"{telemetry['stage2TimeMs']} ms")
    with tel_col5:
        st.metric("Total Execution", f"{telemetry['totalTimeMs']} ms")

    # Split screen for Results List vs Selected Candidate Details
    list_col, details_col = st.columns([2, 3])

    with list_col:
        st.write("#### Top Matching Candidates")
        st.caption("Select a candidate below to view deep-dive professional history and sub-scores:")
        
        # Display list selection
        candidate_options = []
        candidate_map = {}
        for c in top_candidates:
            label = f"#{c['rank']} - {c['name']} ({c['scores']['finalScore']}%)"
            candidate_options.append(label)
            candidate_map[label] = c
            
        if "selected_candidate_id" not in st.session_state or st.session_state.selected_candidate_id is None:
            default_index = 0
        else:
            # find index
            default_index = 0
            for idx, c in enumerate(top_candidates):
                if c["candidate_id"] == st.session_state.selected_candidate_id:
                    default_index = idx
                    break

        selected_label = st.selectbox(
            "Select Candidate to Inspect",
            options=candidate_options,
            index=default_index,
            label_visibility="collapsed"
        )
        
        selected_cand = candidate_map[selected_label]
        st.session_state.selected_candidate_id = selected_cand["candidate_id"]
        
        # Simple mini dataframe table representation
        df_display = []
        for c in top_candidates[:15]:
            df_display.append({
                "Rank": f"#{c['rank']}",
                "Name": c["name"],
                "Headline": c["headline"],
                "Exp": f"{c['experience_years']}y",
                "Match": f"{c['scores']['finalScore']}%"
            })
        st.dataframe(pd.DataFrame(df_display), use_container_width=True, hide_index=True)

        # CSV Export
        st.markdown("<br>", unsafe_allow_html=True)
        
        # CSV generator
        import io
        import csv
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            "Rank", "Candidate ID", "Name", "Headline", "Experience Years", 
            "Education", "Skills", "Final Score", "Semantic Score", 
            "Skill Score", "Career Score", "Behavioral Score", "Reasoning"
        ])
        for c in top_candidates:
            writer.writerow([
                c.get("rank", ""),
                c.get("candidate_id", ""),
                c.get("name", ""),
                c.get("headline", ""),
                c.get("experience_years", ""),
                c.get("education", ""),
                ", ".join(c.get("skills", [])),
                c.get("scores", {}).get("finalScore", ""),
                c.get("scores", {}).get("semanticScore", ""),
                c.get("scores", {}).get("skillScore", ""),
                c.get("scores", {}).get("careerScore", ""),
                c.get("scores", {}).get("behavioralScore", ""),
                c.get("reasoning", "")
            ])
        csv_data = output.getvalue()
        
        st.download_button(
            label="📥 Export Top 100 Match Results to CSV",
            data=csv_data,
            file_name="auratalent_candidate_matches.csv",
            mime="text/csv",
            use_container_width=True
        )

    with details_col:
        st.write(f"#### Profile Inspection: **{selected_cand['name']}**")
        
        # Top Card
        st.markdown(f"""
        <div class="candidate-card">
            <div style="display: flex; justify-content: space-between; align-items: start;">
                <div>
                    <h3 style="margin: 0 0 5px 0; color: white;">{selected_cand['name']}</h3>
                    <p style="margin: 0; color: #cbd5e1; font-weight: 500;">{selected_cand['headline']}</p>
                </div>
                <span class="score-badge">MATCH {selected_cand['scores']['finalScore']}%</span>
            </div>
            <div style="margin-top: 15px; font-size: 0.9rem; color: #94a3b8; display: grid; grid-template-columns: 1fr 1fr; gap: 10px;">
                <div>🎓 {selected_cand['education']}</div>
                <div>💼 Total Experience: {selected_cand['experience_years']} Years</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Sub-scores bars
        st.write("##### Score Composition Breakdown")
        
        score_keys = [
            ("Semantic Text Alignment", "semanticScore", "#818cf8"),
            ("Technical Skill Match", "skillScore", "#34d399"),
            ("Career Progression Score", "careerScore", "#fb7185"),
            ("Behavioral Signal Score", "behavioralScore", "#fbbf24")
        ]
        
        for name, key, color in score_keys:
            val = selected_cand["scores"][key]
            st.markdown(f"""
            <div style="margin-bottom: 8px;">
                <div style="display: flex; justify-content: space-between; font-size: 0.85rem; margin-bottom: 2px;">
                    <span style="color: #94a3b8;">{name}</span>
                    <span style="font-family: 'JetBrains Mono'; font-weight: 600; color: {color};">{val}%</span>
                </div>
                <div style="background-color: #1e293b; height: 8px; border-radius: 9999px;">
                    <div style="background-color: {color}; width: {val}%; height: 100%; border-radius: 9999px;"></div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
        # Skills tags
        st.write("##### Core Professional Skills")
        skills_html = ""
        for s in selected_cand["skills"]:
            skills_html += f'<span style="background-color: #1e293b; color: #cbd5e1; padding: 4px 10px; border-radius: 6px; font-size: 0.8rem; margin-right: 6px; margin-bottom: 6px; display: inline-block; border: 1px solid #334155;">{s}</span>'
        st.markdown(skills_html, unsafe_allow_html=True)

        # Career Timeline
        st.write("##### Professional Career Timeline")
        for j in selected_cand.get("career_history", []):
            st.markdown(f"""
            <div class="timeline-item">
                <div style="font-weight: 600; color: #f1f5f9; font-size: 0.95rem;">{j.get('title')}</div>
                <div style="color: #6366f1; font-size: 0.85rem; font-weight: 500; margin-bottom: 4px;">{j.get('company')}</div>
                <div style="color: #94a3b8; font-size: 0.85rem; line-height: 1.4;">{j.get('description')}</div>
            </div>
            """, unsafe_allow_html=True)

        # Heuristic Reasoning
        st.write("##### Match Pipeline Explanation")
        st.info(selected_cand.get("reasoning", "No heuristic reasoning generated."))

        # Gemini Section
        st.write("##### Deep AI Resume Analysis")
        
        has_api_key = bool(os.environ.get("GEMINI_API_KEY"))
        
        # Check if we already have a generated explanation for this candidate
        exp_cache_key = selected_cand["candidate_id"]
        if "local_ai_explanations" not in st.session_state:
            st.session_state.local_ai_explanations = {}
            
        if exp_cache_key in st.session_state.local_ai_explanations:
            st.success(st.session_state.local_ai_explanations[exp_cache_key])
        else:
            if not has_api_key:
                st.warning("🔑 Configure standard **GEMINI_API_KEY** environment variable to run high-fidelity LLM gap evaluations.")
            
            trigger_gemini = st.button(
                f"🧠 Ask Gemini to Analyze Fit for {selected_cand['name']}",
                type="secondary",
                use_container_width=True,
                disabled=not has_api_key
            )
            
            if trigger_gemini:
                with st.spinner("Invoking Gemini-2.5-Flash for cross-timeline evaluation..."):
                    reasoning_text = generate_gemini_explanation(selected_cand, job_desc_input)
                    st.session_state.local_ai_explanations[exp_cache_key] = reasoning_text
                    st.rerun()
