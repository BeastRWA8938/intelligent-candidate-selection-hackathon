import json
import time
import math
import collections
import re
import csv
from datetime import datetime
import streamlit as st
import pandas as pd

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.absolute()))

import rank
from rank import (
    CONSULTING_COMPANIES, GOOD_TITLES, BAD_TITLES, CONCEPT_CLUSTERS,
    tokenize, get_stop_words, check_disqualifications,
    calculate_meta_scores, get_behavioral_multiplier, generate_reasoning,
    preprocess_text, normalize_skill
)

# Wrapper to keep detailed sieve reasons for the UI expander
def is_honeypot(c, current_time):
    is_hp = rank.is_honeypot(c, current_time)
    if is_hp:
        yoe = c.get("profile", {}).get("years_of_experience", 0.0)
        history = c.get("career_history", [])
        first_start = None
        for job in history:
            sd = job.get("start_date")
            if sd:
                s_dt = rank.parse_date(sd, current_time)
                if s_dt:
                    if first_start is None or s_dt < first_start:
                        first_start = s_dt
        if first_start:
            span_years = (current_time - first_start).days / 365.25
            if yoe > span_years + 2.0:
                return True, "YoE exceeds career dates span by > 2.0 years"
                
        for job in history:
            sd = job.get("start_date")
            ed = job.get("end_date")
            dur = job.get("duration_months", 0.0)
            if sd:
                s_dt = rank.parse_date(sd, current_time)
                if s_dt:
                    if ed:
                        e_dt = rank.parse_date(ed, current_time)
                    else:
                        e_dt = current_time
                    if e_dt:
                        calc_dur = (e_dt - s_dt).days / 30.4
                        if dur > calc_dur + 3.0:
                            return True, f"Job duration mismatch at {job.get('company')}"
                            
        expert_zero_skills = []
        for s in c.get("skills", []):
            prof_level = s.get("proficiency")
            if isinstance(prof_level, str) and prof_level.lower().strip() == "expert":
                dur = s.get("duration_months", 0)
                if dur is None or dur == 0:
                    expert_zero_skills.append(s.get("name", ""))
        if len(expert_zero_skills) >= 4:
            return True, f"Expert skills with 0 duration: {expert_zero_skills}"
            
        return True, "Anomalous profile data detected"
    return False, ""


def make_mock_candidates():
    # 50 high quality mock candidates in case no data is uploaded
    mock_list = []
    for i in range(1, 51):
        cid = f"CAND_10000{i:02d}"
        yoe = float((i % 6) + 4.5) # 4.5 to 9.5
        title_choices = [
            "Senior Machine Learning Engineer", "AI Engineer", "Staff ML Engineer", 
            "Data Scientist", "Software Engineer", "Backend Engineer"
        ]
        curr_title = title_choices[i % len(title_choices)]
        comp_choices = ["TechCorp", "AI Solutions", "StartupHub", "DataFlow", "InnoSystems"]
        curr_company = comp_choices[i % len(comp_choices)]
        loc_choices = ["Pune", "Noida", "Bangalore", "Hyderabad", "Mumbai"]
        loc = loc_choices[i % len(loc_choices)]
        
        # Education
        edu_tier = "tier_1" if i % 3 == 0 else ("tier_2" if i % 3 == 1 else "unknown")
        
        # Skills
        skills = [
            {"name": "Python", "proficiency": "expert", "endorsements": i*2, "duration_months": int(yoe*12)},
            {"name": "embeddings", "proficiency": "expert" if i%2==0 else "advanced", "endorsements": i, "duration_months": 24},
            {"name": "pinecone", "proficiency": "advanced", "endorsements": i % 10, "duration_months": 18},
            {"name": "retrieval", "proficiency": "expert", "endorsements": i % 15, "duration_months": 30},
            {"name": "ndcg", "proficiency": "intermediate", "endorsements": 5, "duration_months": 12}
        ]
        
        # Add some nice to haves
        if i % 4 == 0:
            skills.append({"name": "fine-tuning", "proficiency": "advanced", "endorsements": 3, "duration_months": 10})
        if i % 5 == 0:
            skills.append({"name": "xgboost", "proficiency": "expert", "endorsements": 8, "duration_months": 36})
            
        c = {
            "candidate_id": cid,
            "profile": {
                "anonymized_name": f"Candidate {i}",
                "headline": f"{curr_title} specialized in search and NLP systems",
                "summary": f"Experienced engineer with a history of building production-grade IR and ranking services.",
                "location": loc,
                "country": "India",
                "years_of_experience": yoe,
                "current_title": curr_title,
                "current_company": curr_company,
                "current_company_size": "51-200",
                "current_industry": "Technology"
            },
            "career_history": [
                {
                    "company": curr_company,
                    "title": curr_title,
                    "start_date": "2023-01-01",
                    "end_date": None,
                    "duration_months": int((yoe-2)*12),
                    "is_current": True,
                    "industry": "Technology",
                    "company_size": "51-200",
                    "description": "Led the implementation of hybrid search and dense retrieval pipelines."
                },
                {
                    "company": "PriorSoft",
                    "title": "Software Engineer",
                    "start_date": "2021-01-01",
                    "end_date": "2022-12-31",
                    "duration_months": 24,
                    "is_current": False,
                    "industry": "Technology",
                    "company_size": "201-500",
                    "description": "Developed backend APIs and managed relational databases."
                }
            ],
            "education": [
                {
                    "institution": "IIT Bombay" if edu_tier == "tier_1" else ("BITS Pilani" if edu_tier == "tier_2" else "State University"),
                    "degree": "B.Tech",
                    "field_of_study": "Computer Science",
                    "start_year": 2017,
                    "end_year": 2021,
                    "grade": "8.5 CGPA",
                    "tier": edu_tier
                }
            ],
            "skills": skills,
            "redrob_signals": {
                "profile_completeness_score": 95,
                "signup_date": "2024-01-15",
                "last_active_date": "2026-06-01",
                "open_to_work_flag": True if i % 2 == 0 else False,
                "profile_views_received_30d": i*3,
                "applications_submitted_30d": i % 5,
                "recruiter_response_rate": 0.85 if i % 3 != 0 else 0.20, # some low response rate
                "avg_response_time_hours": 2.5,
                "skill_assessment_scores": {"Python": 92, "retrieval": 88},
                "connection_count": i * 10,
                "endorsements_received": i * 5,
                "notice_period_days": 30 if i % 3 == 0 else (90 if i % 3 == 1 else 60),
                "expected_salary_range_inr_lpa": {"min": 18.0, "max": 30.0},
                "preferred_work_mode": "hybrid",
                "willing_to_relocate": True if i % 2 != 0 else False,
                "github_activity_score": 65 if i % 2 == 0 else 5,
                "search_appearance_30d": i * 4,
                "saved_by_recruiters_30d": i,
                "interview_completion_rate": 0.95,
                "offer_acceptance_rate": 0.80,
                "verified_email": True,
                "verified_phone": True,
                "linkedin_connected": True
            }
        }
        mock_list.append(c)
        
    # Add a couple of honeypots explicitly to show the Sieve in action
    honeypot_1 = {
        "candidate_id": "CAND_9999991",
        "profile": {
            "anonymized_name": "Honeypot Candidate 1",
            "headline": "Expert AI Developer",
            "summary": "Full stack expert",
            "location": "Pune",
            "country": "India",
            "years_of_experience": 10.0,
            "current_title": "AI Engineer",
            "current_company": "FutureAI",
            "current_company_size": "1-10",
            "current_industry": "Technology"
        },
        "career_history": [
            {
                "company": "FutureAI",
                "title": "AI Engineer",
                "start_date": "2025-01-01", # Span is 1.5 years but YoE is 10.0
                "end_date": None,
                "duration_months": 18,
                "is_current": True,
                "industry": "Technology",
                "company_size": "1-10",
                "description": "AI engineer"
            }
        ],
        "education": [],
        "skills": [
            {"name": "Python", "proficiency": "expert", "endorsements": 10, "duration_months": 0} # expert with 0 duration
        ],
        "redrob_signals": {
            "profile_completeness_score": 90,
            "signup_date": "2025-01-01",
            "last_active_date": "2026-06-01",
            "open_to_work_flag": True,
            "profile_views_received_30d": 10,
            "applications_submitted_30d": 1,
            "recruiter_response_rate": 0.9,
            "avg_response_time_hours": 1.0,
            "skill_assessment_scores": {},
            "connection_count": 100,
            "endorsements_received": 10,
            "notice_period_days": 30,
            "expected_salary_range_inr_lpa": {"min": 50.0, "max": 20.0}, # min > max
            "preferred_work_mode": "hybrid",
            "willing_to_relocate": True,
            "github_activity_score": 50,
            "search_appearance_30d": 20,
            "saved_by_recruiters_30d": 5,
            "interview_completion_rate": 1.0,
            "offer_acceptance_rate": 1.0,
            "verified_email": True,
            "verified_phone": True,
            "linkedin_connected": True
        }
    }
    mock_list.append(honeypot_1)
    return mock_list

def run_streamlit_app():
    st.set_page_config(page_title="Redrob Intelligent Candidate Discovery & Ranking Hub", layout="wide")
    
    st.title("🎯 Redrob AI Candidate Discovery & Ranking Hub")
    st.subheader("Senior AI Engineer — Founding Team Pipeline")
    
    st.markdown("""
    This app serves as the verification sandbox for the Intelligent Candidate Discovery & Ranking Challenge. 
    It integrates a multi-layered heuristic pipeline featuring a profile anomaly sieve, concept-clustered skill expansion, 
    TF-IDF semantic analysis, and behavioral availability multipliers.
    """)
    
    current_time = datetime(2026, 6, 18)
    stop_words = get_stop_words()
    
    # ------------------ SIDEBAR CONFIGURATIONS ------------------
    st.sidebar.header("🛠️ Pipeline Configurations")
    
    # Weights playground
    st.sidebar.subheader("Adjust Model Weights")
    w_title = st.sidebar.slider("Current Title Fit Weight", 0.0, 1.0, 0.20, step=0.05)
    w_tfidf = st.sidebar.slider("TF-IDF Keyword Similarity Weight", 0.0, 1.0, 0.30, step=0.05)
    w_skill = st.sidebar.slider("Concept Cluster Skills Weight", 0.0, 1.0, 0.20, step=0.05)
    w_yoe = st.sidebar.slider("Years of Experience (YoE) Fit Weight", 0.0, 1.0, 0.15, step=0.05)
    w_edu = st.sidebar.slider("Education Pedigree Weight", 0.0, 1.0, 0.08, step=0.05)
    w_loc = st.sidebar.slider("Location & Relocation Fit Weight", 0.0, 1.0, 0.07, step=0.05)
    
    total_w = w_title + w_tfidf + w_skill + w_yoe + w_edu + w_loc
    if abs(total_w - 1.0) > 0.01:
        st.sidebar.warning(f"Weights sum to {total_w:.2f}. They will be normalized to sum to 1.0.")
        
    weights = {
        "title": w_title / total_w,
        "tfidf": w_tfidf / total_w,
        "concept_skill": w_skill / total_w,
        "yoe": w_yoe / total_w,
        "edu": w_edu / total_w,
        "loc": w_loc / total_w
    }
    
    st.sidebar.markdown("---")
    st.sidebar.subheader("Data Input Selection")
    data_source = st.sidebar.radio("Select Candidate Pool:", ["Use Interactive Mock Pool (50 Candidates + Traps)", "Upload candidates.jsonl File"])
    
    candidates_raw = []
    if data_source == "Upload candidates.jsonl File":
        uploaded_file = st.sidebar.file_uploader("Upload candidates.jsonl", type=["jsonl", "json"])
        if uploaded_file is not None:
            # Load candidate profiles from the file
            for line in uploaded_file:
                if line.strip():
                    try:
                        candidates_raw.append(json.loads(line))
                    except:
                        pass
            st.sidebar.success(f"Successfully loaded {len(candidates_raw)} candidates from file.")
        else:
            st.sidebar.info("Upload a JSONL file to begin. Falling back to Mock Pool for now.")
            candidates_raw = make_mock_candidates()
    else:
        candidates_raw = make_mock_candidates()
        
    # Execute Pipeline button
    run_pipeline = st.sidebar.button("🚀 Run Discovery & Ranking Engine", type="primary")
    
    # ------------------ TABS SECTION ------------------
    tab1, tab2, tab3 = st.tabs(["📊 Discovery Dashboard", "🕵️ Candidate Profiler", "🧪 Reasoning Playground"])
    
    # Pre-scoring variables (using session state to keep data)
    if "ranked_data" not in st.session_state:
        st.session_state.ranked_data = None
    if "sieved_out" not in st.session_state:
        st.session_state.sieved_out = []
        
    if run_pipeline:
        with st.spinner("Processing candidates (Sieving traps, parsing TF-IDF, clustering skills, applying multipliers)..."):
            sieved_out = []
            qualified_candidates = []
            df_words = collections.defaultdict(int)
            
            # Layer 1: Sieve
            for c in candidates_raw:
                cid = c["candidate_id"]
                
                # Check honeypot
                hp, hp_reason = is_honeypot(c, current_time)
                if hp:
                    sieved_out.append({"candidate_id": cid, "reason": f"Honeypot: {hp_reason}", "details": c})
                    continue
                    
                # Check disqualifications
                disq, disq_reason = check_disqualifications(c)
                if disq:
                    sieved_out.append({"candidate_id": cid, "reason": f"Disqualified: {disq_reason}", "details": c})
                    continue
                    
                # Tokenize for TF-IDF
                prof = c["profile"]
                summary = prof.get("summary", "")
                headline = prof.get("headline", "")
                current_title = prof.get("current_title", "")
                skills_str = " ".join([s["name"] for s in c.get("skills", [])])
                
                combined_text = f"{current_title} {headline} {summary} {skills_str}"
                tokens = [w for w in tokenize(combined_text) if w not in stop_words]
                tf = collections.Counter(tokens)
                
                qualified_candidates.append((c, tf))
                for word in tf.keys():
                    df_words[word] += 1
            
            # Layer 2: TF-IDF calculation
            N = len(qualified_candidates)
            if N > 0:
                idf = {}
                for word, count in df_words.items():
                    idf[word] = math.log(1.0 + (N / (1.0 + count)))
                    
                # JD TF-IDF vector
                jd_text = """
                Senior AI Engineer — Founding Team. Modern ML systems, embeddings, retrieval, ranking, LLMs, fine-tuning.
                embeddings-based retrieval systems (sentence-transformers, OpenAI embeddings, BGE, E5, or similar).
                vector databases or hybrid search infrastructure — Pinecone, Weaviate, Qdrant, Milvus, OpenSearch, Elasticsearch, FAISS.
                designing evaluation frameworks for ranking systems — NDCG, MRR, MAP.
                Strong Python.
                """
                jd_tokens = [w for w in tokenize(jd_text) if w not in stop_words]
                jd_tf = collections.Counter(jd_tokens)
                
                jd_vector = {}
                jd_norm = 0.0
                for word, tf_val in jd_tf.items():
                    if word in idf:
                        weight = tf_val * idf[word]
                        jd_vector[word] = weight
                        jd_norm += weight * weight
                jd_norm = math.sqrt(jd_norm)
                
                # Raw similarity values
                raw_similarities = []
                for c, tf in qualified_candidates:
                    dot_product = 0.0
                    doc_norm = 0.0
                    for word, tf_val in tf.items():
                        weight = tf_val * idf[word]
                        doc_norm += weight * weight
                        if word in jd_vector:
                            dot_product += weight * jd_vector[word]
                    doc_norm = math.sqrt(doc_norm)
                    
                    sim = 0.0
                    if doc_norm > 0.0 and jd_norm > 0.0:
                        sim = dot_product / (doc_norm * jd_norm)
                    raw_similarities.append(sim)
                    
                max_sim = max(raw_similarities) if raw_similarities else 1.0
                
                # Full Scoring
                scored_candidates = []
                for i, (c, tf) in enumerate(qualified_candidates):
                    cid = c["candidate_id"]
                    sim = raw_similarities[i]
                    tfidf_score = (sim / max_sim) * 100.0
                    
                    # Meta scores
                    meta = calculate_meta_scores(c, weights, current_time)
                    
                    base_score = (
                        (weights["title"] * meta["title"]) +
                        (weights["tfidf"] * tfidf_score) +
                        (weights["concept_skill"] * meta["concept_skill"]) +
                        (weights["yoe"] * meta["yoe"]) +
                        (weights["edu"] * meta["edu"]) +
                        (weights["loc"] * meta["loc"])
                    )
                    
                    behavioral = get_behavioral_multiplier(c["redrob_signals"], current_time)
                    final_score = base_score * behavioral["composite"]
                    
                    location = c["profile"].get("location", "").lower()
                    is_pune_noida = "pune" in location or "noida" in location or "delhi ncr" in location or "ncr" in location
                    notice = c["redrob_signals"].get("notice_period_days", 60)
                    
                    reasoning = generate_reasoning(c, c["profile"]["years_of_experience"], meta["matched_skills"], is_pune_noida, notice, c["redrob_signals"])
                    
                    scored_candidates.append({
                        "candidate_id": cid,
                        "score": round(final_score, 3),
                        "base_score": round(base_score, 3),
                        "meta_breakdown": {**meta, "tfidf": tfidf_score},
                        "behavioral_breakdown": behavioral,
                        "reasoning": reasoning,
                        "details": c
                    })
                    
                # Deterministic sorting: score descending, then candidate_id ascending for ties
                scored_candidates.sort(key=lambda x: (-x["score"], x["candidate_id"]))
                
                st.session_state.ranked_data = scored_candidates
                st.session_state.sieved_out = sieved_out
            else:
                st.error("No candidates qualified after Sieve stage!")
                
    # ------------------ TAB 1: DASHBOARD ------------------
    with tab1:
        if st.session_state.ranked_data is not None:
            # Metrics
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Candidates Screened", len(candidates_raw))
            c2.metric("Filtered (Disqualified/Honeypot)", len(st.session_state.sieved_out))
            c3.metric("Qualified Candidates", len(st.session_state.ranked_data))
            c4.metric("Top Candidate Score", f"{st.session_state.ranked_data[0]['score']:.1f}")
            
            st.markdown("### 🏆 Top Ranked Candidates")
            
            # Build display dataframe
            rows = []
            for rank_val, item in enumerate(st.session_state.ranked_data, 1):
                c = item["details"]
                rows.append({
                    "Rank": rank_val,
                    "ID": item["candidate_id"],
                    "Name": c["profile"]["anonymized_name"],
                    "Current Title": c["profile"]["current_title"],
                    "Company": c["profile"]["current_company"],
                    "YoE": c["profile"]["years_of_experience"],
                    "Location": c["profile"]["location"],
                    "Score": item["score"],
                    "Reasoning": item["reasoning"]
                })
            df_disp = pd.DataFrame(rows)
            
            # Truncate reasoning in UI for scanability
            df_disp_truncated = df_disp.copy()
            df_disp_truncated["Reasoning"] = df_disp_truncated["Reasoning"].apply(
                lambda x: x[:80] + "..." if len(x) > 80 else x
            )
            st.dataframe(df_disp_truncated.set_index("Rank"), height=400, use_container_width=True)
            
            # Export CSV (using full reasoning)
            csv_buf = df_disp[["ID", "Rank", "Score", "Reasoning"]].rename(
                columns={"ID": "candidate_id", "Rank": "rank", "Score": "score", "Reasoning": "reasoning"}
            ).to_csv(index=False)
            st.download_button(
                label="📥 Download Submission CSV (Top 100 format)",
                data=csv_buf,
                file_name="team_redrob_streamlit.csv",
                mime="text/csv"
            )
            
            # Sieved out section
            if st.session_state.sieved_out:
                with st.expander("🚫 Inspect Filtered / Disqualified Candidates"):
                    sieve_rows = []
                    for item in st.session_state.sieved_out:
                        c = item["details"]
                        sieve_rows.append({
                            "ID": item["candidate_id"],
                            "Name": c["profile"]["anonymized_name"],
                            "Title": c["profile"]["current_title"],
                            "Reason for Filtration": item["reason"]
                        })
                    st.table(pd.DataFrame(sieve_rows))
        else:
            st.info("👈 Please select your candidate pool in the sidebar and click 'Run Discovery & Ranking Engine' to process and view rankings.")
            
    # ------------------ TAB 2: PROFILER ------------------
    with tab2:
        if st.session_state.ranked_data is not None:
            st.markdown("### 🔍 In-depth Candidate Profiling & Audit")
            
            # Selector
            cids_list = [item["candidate_id"] for item in st.session_state.ranked_data]
            selected_cid = st.selectbox("Select a Candidate to Profile:", cids_list)
            
            # Find item
            item = next(x for x in st.session_state.ranked_data if x["candidate_id"] == selected_cid)
            c = item["details"]
            meta = item["meta_breakdown"]
            beh = item["behavioral_breakdown"]
            
            col1, col2 = st.columns([1, 1])
            
            with col1:
                st.markdown(f"#### 📄 {c['profile']['anonymized_name']} ({selected_cid})")
                st.markdown(f"**Headline:** {c['profile']['headline']}")
                st.markdown(f"**Current Title:** {c['profile']['current_title']} at **{c['profile']['current_company']}**")
                st.markdown(f"**Experience:** {c['profile']['years_of_experience']} Years")
                st.markdown(f"**Location:** {c['profile']['location']} ({c['profile']['country']})")
                st.markdown(f"**Industry:** {c['profile']['current_industry']} | size: {c['profile']['current_company_size']}")
                
                st.markdown("##### 💼 Career History")
                for job in c["career_history"]:
                    st.markdown(f"- **{job['title']}** at *{job['company']}* ({job['start_date']} to {job['end_date'] or 'Present'}) — {job['duration_months']} months")
                    st.markdown(f"  *Description:* {job['description']}")
                    
                st.markdown("##### 🎓 Education")
                for edu in c["education"]:
                    st.markdown(f"- **{edu['degree']} in {edu['field_of_study']}**")
                    st.markdown(f"  *{edu['institution']}* (Tier: {edu.get('tier', 'unknown')} | {edu['start_year']}-{edu['end_year']})")
                    
            with col2:
                st.markdown("#### ⚡ Scoring Audit Breakdown")
                st.metric("Final Adjusted Score", f"{item['score']:.3f}", help="Base Match Score * Behavioral Multiplier")
                st.markdown(f"**Base Match Score:** {item['base_score']:.3f} / 100.0")
                
                # Base breakdown
                st.markdown("**Base Components (out of 100.0 each):**")
                c_sub1, c_sub2, c_sub3 = st.columns(3)
                c_sub1.metric("Title Score", f"{meta['title']:.1f}")
                c_sub2.metric("Skill Score", f"{meta['concept_skill']:.1f}")
                c_sub3.metric("YoE Score", f"{meta['yoe']:.1f}")
                
                c_sub4, c_sub5, c_sub6 = st.columns(3)
                c_sub4.metric("Education Tier", f"{meta['edu']:.1f}")
                c_sub5.metric("Location Score", f"{meta['loc']:.1f}")
                c_sub6.metric("TF-IDF Similarity", f"{meta.get('tfidf', 0.0):.1f}")
                
                # Multipliers
                st.markdown("##### ⚙️ Availability Multipliers")
                st.write(f"- **Total Behavioral Modifier:** `{beh['composite']:.3f}x`")
                st.write(f"  - Recruiter Response Rate Modifier: `{beh['breakdown']['response_mult']:.2f}x` (Response Rate: {int(c['redrob_signals'].get('recruiter_response_rate', 0.5)*100)}%)")
                st.write(f"  - Platform Activity Modifier: `{beh['breakdown']['activity_mult']:.2f}x` (Last Active: {c['redrob_signals'].get('last_active_date')})")
                st.write(f"  - Stated Notice Period Modifier: `{beh['breakdown']['notice_mult']:.2f}x` ({c['redrob_signals'].get('notice_period_days', 60)} days)")
                st.write(f"  - Open-to-work Flag Modifier: `{beh['breakdown']['open_to_work_mult']:.2f}x` (`{c['redrob_signals'].get('open_to_work_flag')}`)")
                st.write(f"  - GitHub Activity Modifier: `{beh['breakdown']['github_mult']:.2f}x` (Activity Score: {c['redrob_signals'].get('github_activity_score')})")
                
                st.markdown("##### 💡 AI Recruiter Reasoning")
                st.info(item["reasoning"])
        else:
            st.info("👈 Please execute the pipeline in the sidebar to populate candidate profiles.")
            
    # ------------------ TAB 3: PLAYGROUND ------------------
    with tab3:
        st.markdown("### 🧪 Dynamic Reasoning Generator Playground")
        st.markdown("""
        Test the reasoning engine's capability to generate fluid, non-templated summaries. 
        Adjust the candidate profile attributes below to see how the engine instantly crafts an audit.
        """)
        
        # Candidate Profile builder
        col_p1, col_p2 = st.columns(2)
        
        with col_p1:
            play_cid = st.text_input("Candidate ID:", value="CAND_0099881")
            play_name = st.text_input("Candidate Anonymized Name:", value="Anonymized Candidate")
            play_yoe = st.slider("Years of Experience (YoE):", 0.0, 20.0, 7.5, step=0.5)
            play_title = st.text_input("Current Job Title:", value="Senior Machine Learning Engineer")
            play_company = st.text_input("Current Company Name:", value="NeuralForge AI")
            play_location = st.selectbox("Current Location:", ["Pune", "Noida", "Bangalore", "Hyderabad", "Delhi NCR", "Chennai", "Remote"])
            play_relocate = st.checkbox("Willing to Relocate to Pune/Noida Office", value=True)
            
        with col_p2:
            play_skills = st.multiselect(
                "Matched Core Skills:", 
                ["embeddings", "retrieval", "pinecone", "weaviate", "sentence-transformers", "ndcg", "mrr", "map", "pytorch", "transformers", "fine-tuning", "xgboost"],
                default=["embeddings", "retrieval", "pinecone"]
            )
            play_notice = st.slider("Notice Period (Days):", 0, 180, 45, step=15)
            play_response_rate = st.slider("Recruiter Response Rate (%):", 0, 100, 85, step=5)
            play_active_date = st.date_input("Last Active Date:", datetime(2026, 6, 1))
            
        # Calculate flags
        is_pune_noida = play_location.lower() in ["pune", "noida", "delhi ncr", "ncr"]
        notice_days = play_notice
        resp_rate = play_response_rate / 100.0
        
        mock_c = {
            "candidate_id": play_cid,
            "profile": {
                "anonymized_name": play_name,
                "current_title": play_title,
                "current_company": play_company,
                "location": play_location
            },
            "skills": [{"name": s} for s in play_skills],
            "redrob_signals": {
                "recruiter_response_rate": resp_rate,
                "notice_period_days": notice_days,
                "willing_to_relocate": play_relocate,
                "last_active_date": play_active_date.strftime("%Y-%m-%d")
            }
        }
        
        # Generate and show reasoning
        st.markdown("#### 💬 Generated Reasoning Output")
        reasoning_out = generate_reasoning(
            mock_c, play_yoe, play_skills, is_pune_noida, notice_days, mock_c["redrob_signals"]
        )
        st.success(reasoning_out)
        
        # Word and sentence counts
        words = reasoning_out.split()
        sentences = re.split(r'\. |\? |\! ', reasoning_out)
        st.write(f"ℹ️ **Reasoning Stats:** {len(sentences)} sentences, {len(words)} words. Dynamic seed from ID: `{sum(ord(c) for c in play_cid)}`.")
        
if __name__ == "__main__":
    run_streamlit_app()
