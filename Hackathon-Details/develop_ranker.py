import os
import json
from datetime import datetime

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Define lists of consulting companies and valid/invalid titles
CONSULTING_COMPANIES = {
    "tcs", "tata consultancy services", "infosys", "wipro", "accenture", 
    "cognizant", "capgemini", "hcl", "tech mahindra", "l&t", "lnt", 
    "mindtree", "mphasis", "ust global", "hexaware"
}

GOOD_TITLES = {
    "ai engineer", "machine learning engineer", "ml engineer", "applied ml engineer",
    "recommendation systems engineer", "search engineer", "nlp engineer",
    "data scientist", "backend engineer", "software engineer", "full stack developer",
    "systems engineer", "applied machine learning engineer", "computer vision engineer",
    "mlops engineer", "principal machine learning engineer", "lead machine learning engineer",
    "senior machine learning engineer", "senior ai engineer", "senior ml engineer",
    "senior data scientist", "senior backend engineer", "senior software engineer"
}

BAD_TITLES = {
    "graphic designer", "mechanical engineer", "operations manager", "marketing manager",
    "accountant", "sales executive", "hr specialist", "customer support",
    "financial analyst", "content writer", "product manager", "ux designer", "ui designer",
    "marketing specialist", "recruiter", "sales manager", "business development manager"
}

CORE_SKILLS = {
    "embeddings", "retrieval", "ranking", "sentence-transformers", "pinecone", 
    "weaviate", "qdrant", "milvus", "faiss", "elasticsearch", "hybrid search", 
    "ndcg", "mrr", "map", "evaluation", "vector search", "information retrieval",
    "mlops", "xgboost", "lightgbm", "pytorch", "tensorflow", "transformers"
}

def is_honeypot(c, current_time):
    # Rule 1: YoE vs First Job Start Date
    yoe = c["profile"]["years_of_experience"]
    history = c["career_history"]
    first_start = None
    for job in history:
        sd = job.get("start_date")
        if sd:
            try:
                s_dt = datetime.strptime(sd, "%Y-%m-%d")
                if first_start is None or s_dt < first_start:
                    first_start = s_dt
            except:
                pass
    if first_start:
        span_years = (current_time - first_start).days / 365.25
        if yoe > span_years + 0.5:
            return True, "YoE exceeds job dates span"
            
    # Rule 2: Job duration stated vs calendar span
    for job in history:
        sd = job.get("start_date")
        ed = job.get("end_date")
        dur = job.get("duration_months", 0)
        if sd:
            try:
                s_dt = datetime.strptime(sd, "%Y-%m-%d")
                if ed:
                    e_dt = datetime.strptime(ed, "%Y-%m-%d")
                else:
                    e_dt = current_time
                calc_dur = (e_dt - s_dt).days / 30.4
                if dur > calc_dur + 3:
                    return True, f"Job duration mismatch at {job['company']}"
            except:
                pass
                
    # Rule 3: Expert skills with 0 duration
    expert_zero_skills = [s["name"] for s in c.get("skills", []) if s.get("proficiency") == "expert" and s.get("duration_months", 0) == 0]
    if len(expert_zero_skills) >= 1:
        return True, f"Expert skill with 0 duration: {expert_zero_skills}"
        
    return False, ""

def score_candidate(c, current_time):
    # 1. Check if honeypot
    hp, hp_reason = is_honeypot(c, current_time)
    if hp:
        return 0.0, f"Disqualified: Honeypot ({hp_reason})"
        
    # Extract profile details
    prof = c["profile"]
    curr_title = prof.get("current_title", "").lower()
    curr_company = prof.get("current_company", "").lower()
    yoe = prof.get("years_of_experience", 0)
    location = prof.get("location", "").lower()
    country = prof.get("country", "").lower()
    
    # Extract career history
    history = c["career_history"]
    
    # Extract skills
    skills = c.get("skills", [])
    skill_names = [s["name"].lower() for s in skills]
    
    # Extract signals
    signals = c["redrob_signals"]
    
    # Rule A: Current Title Disqualification (Trap Candidates)
    if curr_title in BAD_TITLES:
        return 0.0, f"Disqualified: Irrelevant current title ({curr_title})"
        
    # Rule B: Consulting Firms only Disqualification
    all_consulting = True
    for job in history:
        comp = job.get("company", "").lower()
        # Clean company name
        is_consulting = any(cs in comp for cs in CONSULTING_COMPANIES)
        if not is_consulting:
            all_consulting = False
            break
    if all_consulting and history:
        return 0.0, "Disqualified: Only worked at consulting firms"
        
    # Rule C: Under 12 months AI experience using LangChain/OpenAI only (Pure research / LangChain-only)
    # If the candidate has RAG/LangChain/OpenAI but no core ML skills
    has_core_ml = False
    for s in skill_names:
        if s in CORE_SKILLS:
            has_core_ml = True
            break
    
    # Score component 1: Title Relevance
    title_score = 0.0
    if any(gt in curr_title for gt in GOOD_TITLES):
        title_score = 100.0
    elif "engineer" in curr_title or "developer" in curr_title or "programmer" in curr_title:
        title_score = 60.0
    else:
        title_score = 20.0
        
    # Score component 2: Skills Match
    skill_score = 0.0
    matched_core_skills = []
    for s in skills:
        s_name = s["name"].lower()
        if s_name in CORE_SKILLS:
            prof_level = s.get("proficiency", "beginner")
            prof_mult = {"beginner": 0.5, "intermediate": 0.8, "advanced": 1.0, "expert": 1.2}[prof_level]
            dur = s.get("duration_months", 0)
            # Endorsements
            end = s.get("endorsements", 0)
            end_mult = min(1.5, 1.0 + (end / 50.0))
            
            # Score contribution
            s_score = 10.0 * prof_mult * end_mult * (min(36.0, dur) / 12.0)
            skill_score += s_score
            matched_core_skills.append(s["name"])
            
    # Score component 3: Experience
    # Target 5-9 years.
    if 5.0 <= yoe <= 9.0:
        yoe_score = 100.0
    elif 4.0 <= yoe < 5.0:
        yoe_score = 80.0
    elif 9.0 < yoe <= 11.0:
        yoe_score = 80.0
    elif 3.0 <= yoe < 4.0:
        yoe_score = 50.0
    elif 11.0 < yoe <= 13.0:
        yoe_score = 50.0
    else:
        yoe_score = 10.0
        
    # Score component 4: Pedigree (Education Tier)
    edu_score = 50.0 # baseline
    for edu in c.get("education", []):
        tier = edu.get("tier", "unknown")
        if tier == "tier_1":
            edu_score = max(edu_score, 100.0)
        elif tier == "tier_2":
            edu_score = max(edu_score, 80.0)
            
    # Score component 5: Location / Relocation
    loc_score = 50.0
    # Pune / Noida are target offices
    is_pune_noida = "pune" in location or "noida" in location or "delhi ncr" in location or "ncr" in location
    is_tier1_india = any(city in location for city in ["hyderabad", "mumbai", "bangalore", "bengaluru", "chennai"])
    
    if is_pune_noida:
        loc_score = 100.0
    elif is_tier1_india and signals.get("willing_to_relocate", False):
        loc_score = 80.0
    elif is_tier1_india:
        loc_score = 60.0
    elif signals.get("willing_to_relocate", False):
        loc_score = 50.0
        
    # Base match score
    base_score = (title_score * 0.35) + (skill_score * 0.35) + (yoe_score * 0.15) + (edu_score * 0.08) + (loc_score * 0.07)
    
    # Score component 6: Behavioral Signals Modifier
    # Recruiter response rate (avg ~ 0.5)
    resp_rate = signals.get("recruiter_response_rate", 0.5)
    resp_mult = 0.7 + (resp_rate * 0.6) # maps 0.0->0.7 to 1.0->1.3
    
    # Last active date: active within last 30 days is best
    last_act = signals.get("last_active_date")
    act_mult = 1.0
    if last_act:
        try:
            la_dt = datetime.strptime(last_act, "%Y-%m-%d")
            days_inactive = (current_time - la_dt).days
            if days_inactive <= 30:
                act_mult = 1.2
            elif days_inactive <= 90:
                act_mult = 1.0
            elif days_inactive <= 180:
                act_mult = 0.8
            else:
                act_mult = 0.4 # heavily penalize inactive for >6 months
        except:
            pass
            
    # Notice period: shorter notice period is better
    notice = signals.get("notice_period_days", 60)
    if notice <= 30:
        notice_mult = 1.1
    elif notice <= 60:
        notice_mult = 1.0
    elif notice <= 90:
        notice_mult = 0.8
    else:
        notice_mult = 0.6
        
    # Open to work flag
    otw_mult = 1.1 if signals.get("open_to_work_flag", False) else 0.95
    
    # Github activity
    gh_score = signals.get("github_activity_score", -1)
    if gh_score >= 50:
        gh_mult = 1.1
    elif gh_score >= 10:
        gh_mult = 1.0
    else:
        gh_mult = 0.9
        
    final_score = base_score * resp_mult * act_mult * notice_mult * otw_mult * gh_mult
    
    # Construct reasoning
    reason = f"Senior AI Engineer with {yoe:.1f}y experience matching core skills ({', '.join(matched_core_skills[:3])}). "
    if is_pune_noida:
        reason += f"Located in Pune/Noida region. "
    elif signals.get("willing_to_relocate", False):
        reason += f"Willing to relocate to Pune/Noida office. "
    reason += f"Strong platform engagement (active {signals.get('last_active_date')})."
    
    return final_score, reason

def test_ranking():
    current_time = datetime(2026, 6, 18)
    scored_candidates = []
    
    with open(os.path.join(PROJECT_ROOT, "Hackathon-Details", "candidates.jsonl"), "r", encoding="utf-8") as f:
        for idx, line in enumerate(f):
            c = json.loads(line)
            score, reason = score_candidate(c, current_time)
            if score > 0:
                scored_candidates.append((c["candidate_id"], score, reason, c))
            if idx > 0 and idx % 20000 == 0:
                print(f"Processed {idx}...")
                
    # Sort and rank
    scored_candidates.sort(key=lambda x: x[1], reverse=True)
    
    print(f"\nTotal qualified candidates: {len(scored_candidates)}")
    print("\nTop 10 ranked candidates:")
    for rank, (cid, score, reason, c) in enumerate(scored_candidates[:10], 1):
        print(f"{rank}. {cid} | Score={score:.2f} | Title='{c['profile']['current_title']}' | YoE={c['profile']['years_of_experience']} | Loc={c['profile']['location']}")
        print(f"  Reasoning: {reason}")
        print(f"  Signals: Active={c['redrob_signals']['last_active_date']}, ResponseRate={c['redrob_signals']['recruiter_response_rate']}, Notice={c['redrob_signals']['notice_period_days']}d")

if __name__ == "__main__":
    test_ranking()