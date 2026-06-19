import json
import time
import math
import collections
import re
from datetime import datetime

# Consulting companies set
CONSULTING_COMPANIES = {
    "tcs", "tata consultancy services", "infosys", "wipro", "accenture", 
    "cognizant", "capgemini", "hcl", "tech mahindra", "l&t", "lnt", 
    "mindtree", "mphasis", "ust global", "hexaware"
}

# Good titles
GOOD_TITLES = {
    "ai engineer", "machine learning engineer", "ml engineer", "applied ml engineer",
    "recommendation systems engineer", "search engineer", "nlp engineer",
    "data scientist", "backend engineer", "software engineer", "full stack developer",
    "systems engineer", "applied machine learning engineer", "computer vision engineer",
    "mlops engineer", "principal machine learning engineer", "lead machine learning engineer",
    "senior machine learning engineer", "senior ai engineer", "senior ml engineer",
    "senior data scientist", "senior backend engineer", "senior software engineer"
}

# Disqualified titles (for trap candidates)
BAD_TITLES = {
    "graphic designer", "mechanical engineer", "operations manager", "marketing manager",
    "accountant", "sales executive", "hr specialist", "customer support",
    "financial analyst", "content writer", "product manager", "ux designer", "ui designer",
    "marketing specialist", "recruiter", "sales manager", "business development manager"
}

# Concept Clusters for robust skill matching
CONCEPT_CLUSTERS = {
    "retrieval_search": {"embeddings", "retrieval", "dense retrieval", "hybrid search", "vector search", "information retrieval", "search", "elasticsearch", "opensearch", "bm25"},
    "vector_dbs": {"pinecone", "weaviate", "qdrant", "milvus", "faiss", "chroma"},
    "models_frameworks": {"sentence-transformers", "bert", "transformers", "pytorch", "tensorflow", "huggingface", "llm", "llms", "gans", "yolo", "diffusion models", "rag"},
    "evaluation": {"ndcg", "mrr", "map", "evaluation", "offline evaluation", "ab testing"}
}

def tokenize(text):
    return re.findall(r"\b[a-z]{2,}\b", text.lower())

def get_stop_words():
    return {
        'i', 'me', 'my', 'myself', 'we', 'our', 'ours', 'ourselves', 'you', 'your', 'yours', 
        'yourself', 'yourselves', 'he', 'him', 'his', 'himself', 'she', 'her', 'hers', 
        'herself', 'it', 'its', 'itself', 'they', 'them', 'their', 'theirs', 'themselves', 
        'what', 'which', 'who', 'whom', 'this', 'that', 'these', 'those', 'am', 'is', 'are', 
        'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'having', 'do', 'does', 
        'did', 'doing', 'a', 'an', 'the', 'and', 'but', 'if', 'or', 'because', 'as', 'until', 
        'while', 'of', 'at', 'by', 'for', 'with', 'about', 'against', 'between', 'into', 
        'through', 'during', 'before', 'after', 'above', 'below', 'to', 'from', 'up', 'down', 
        'in', 'out', 'on', 'off', 'over', 'under', 'again', 'further', 'then', 'once', 'here', 
        'there', 'when', 'where', 'why', 'how', 'all', 'any', 'both', 'each', 'few', 'more', 
        'most', 'other', 'some', 'such', 'no', 'nor', 'not', 'only', 'own', 'same', 'so', 
        'than', 'too', 'very', 's', 't', 'can', 'will', 'just', 'don', 'should', 'now'
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
            return True
            
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
                    return True
            except:
                pass
                
    # Rule 3: Expert skills with 0 duration
    expert_zero_skills = [s["name"] for s in c.get("skills", []) if s.get("proficiency") == "expert" and s.get("duration_months", 0) == 0]
    if len(expert_zero_skills) >= 1:
        return True
        
    return False

def check_disqualifications(c):
    prof = c["profile"]
    curr_title = prof.get("current_title", "").lower()
    history = c["career_history"]
    
    # 1. Bad Title
    if curr_title in BAD_TITLES:
        return True, "Irrelevant current title (Graphic Designer/Mechanical Eng/etc.)"
        
    # 2. Consulting firm only
    all_consulting = True
    for job in history:
        comp = job.get("company", "").lower().strip()
        is_consult = any(cs in comp for cs in CONSULTING_COMPANIES)
        if not is_consult:
            all_consulting = False
            break
    if all_consulting and history:
        return True, "Only worked at consulting/services firms"
        
    return False, ""

def calculate_meta_scores(c, current_time):
    prof = c["profile"]
    curr_title = prof.get("current_title", "").lower()
    yoe = prof.get("years_of_experience", 0)
    location = prof.get("location", "").lower()
    signals = c["redrob_signals"]
    skills = c.get("skills", [])
    skill_names_set = {s["name"].lower() for s in skills}
    
    # 1. Title Score
    title_score = 0.0
    if any(gt in curr_title for gt in GOOD_TITLES):
        title_score = 100.0
    elif "engineer" in curr_title or "developer" in curr_title or "programmer" in curr_title:
        title_score = 60.0
    else:
        title_score = 20.0
        
    # 2. Concept Skill Score (using Clusters)
    matched_clusters = 0
    skills_weighted = 0.0
    matched_skills = []
    
    for cluster_name, keywords in CONCEPT_CLUSTERS.items():
        overlap = skill_names_set.intersection(keywords)
        if overlap:
            matched_clusters += 1
            # Add weights for skills inside the cluster
            for s in skills:
                s_name = s["name"].lower()
                if s_name in overlap:
                    prof_level = s.get("proficiency", "beginner")
                    prof_mult = {"beginner": 0.5, "intermediate": 0.8, "advanced": 1.0, "expert": 1.2}[prof_level]
                    dur = s.get("duration_months", 0)
                    end = s.get("endorsements", 0)
                    end_mult = min(1.5, 1.0 + (end / 50.0))
                    
                    s_score = 10.0 * prof_mult * end_mult * (min(36.0, dur) / 12.0)
                    skills_weighted += s_score
                    matched_skills.append(s["name"])
                    
    # Cluster multiplier: reward having skills across multiple distinct clusters (e.g. databases + evaluation)
    cluster_mult = 0.4 + (matched_clusters * 0.15) # 1->0.55, 2->0.70, 3->0.85, 4->1.0
    concept_skill_score = min(100.0, skills_weighted * cluster_mult * 3.0)
    
    # 3. Experience Score (5-9 years target)
    if 5.0 <= yoe <= 9.0:
        yoe_score = 100.0
    elif 4.0 <= yoe < 5.0 or 9.0 < yoe <= 11.0:
        yoe_score = 80.0
    elif 3.0 <= yoe < 4.0 or 11.0 < yoe <= 13.0:
        yoe_score = 50.0
    else:
        yoe_score = 10.0
        
    # 4. Pedigree Score
    edu_score = 50.0
    for edu in c.get("education", []):
        tier = edu.get("tier", "unknown")
        if tier == "tier_1":
            edu_score = max(edu_score, 100.0)
        elif tier == "tier_2":
            edu_score = max(edu_score, 80.0)
            
    # 5. Location Score (Pune/Noida focus)
    loc_score = 50.0
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
        
    return {
        "title": title_score,
        "concept_skill": concept_skill_score,
        "yoe": yoe_score,
        "edu": edu_score,
        "loc": loc_score,
        "matched_skills": matched_skills
    }

def get_behavioral_multiplier(signals, current_time):
    # Recruiter response rate modifier
    resp_rate = signals.get("recruiter_response_rate", 0.5)
    resp_mult = 0.7 + (resp_rate * 0.6) # maps 0.0->0.7 to 1.0->1.3
    
    # Activity decay
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
                act_mult = 0.4
        except:
            pass
            
    # Notice period
    notice = signals.get("notice_period_days", 60)
    if notice <= 30:
        notice_mult = 1.15
    elif notice <= 60:
        notice_mult = 1.0
    elif notice <= 90:
        notice_mult = 0.8
    else:
        notice_mult = 0.5
        
    # Open to work
    otw_mult = 1.1 if signals.get("open_to_work_flag", False) else 0.95
    
    # Github activity
    gh_score = signals.get("github_activity_score", -1)
    if gh_score >= 50:
        gh_mult = 1.1
    elif gh_score >= 10:
        gh_mult = 1.0
    else:
        gh_mult = 0.9
        
    return resp_mult * act_mult * notice_mult * otw_mult * gh_mult

def generate_reasoning(c, yoe, matched_skills, is_pune_noida, notice, signals):
    nice_to_haves = []
    skills_lower = [s["name"].lower() for s in c.get("skills", [])]
    if "fine-tuning" in "".join(skills_lower) or "lora" in "".join(skills_lower):
        nice_to_haves.append("LLM fine-tuning")
    if "xgboost" in skills_lower or "lightgbm" in skills_lower or "learning to rank" in "".join(skills_lower):
        nice_to_haves.append("learning-to-rank")
    if "distributed systems" in "".join(skills_lower) or "spark" in skills_lower:
        nice_to_haves.append("distributed systems")
        
    current_title = c["profile"]["current_title"]
    current_company = c["profile"]["current_company"]
    
    # Location phrasing
    if is_pune_noida:
        loc_str = "Pune/Noida-based"
    elif signals.get("willing_to_relocate", False):
        loc_str = "willing to relocate to Pune/Noida"
    else:
        loc_str = f"based in {c['profile']['location']}"
        
    # Active phrasing
    last_act = signals.get("last_active_date", "")
    active_str = "highly active on the platform" if last_act >= "2026-05-01" else "moderately active"
    
    # Concern phrasing
    concern_str = ""
    if notice >= 90:
        concern_str = f"though notice period of {notice} days is longer than preferred"
    elif signals.get("recruiter_response_rate", 1.0) < 0.35:
        concern_str = "though low response rate is a minor availability concern"
        
    skills_str = ", ".join(matched_skills[:2]) if matched_skills else "matching ML tools"
    
    parts = []
    parts.append(f"Senior candidate with {yoe:.1f} years of experience, currently working as {current_title} at {current_company}.")
    
    fit_sentence = f"Demonstrates strong hands-on experience in {skills_str}"
    if nice_to_haves:
        fit_sentence += f" along with exposure to {nice_to_haves[0]}"
    fit_sentence += f", and is {loc_str}."
    parts.append(fit_sentence)
    
    if concern_str:
        parts.append(f"Highly relevant profile, {concern_str}.")
    else:
        parts.append(f"Strong fit due to fast response rate ({int(signals.get('recruiter_response_rate', 0.5)*100)}%) and {active_str}.")
        
    return " ".join(parts)

def main():
    start_time = time.time()
    current_time = datetime(2026, 6, 18)
    
    print("Layer 1: Pre-computing TF-IDF vectors for all candidates...")
    stop_words = get_stop_words()
    
    # Build vocabulary and document counts
    texts = []
    candidates = []
    cids = []
    
    df = collections.defaultdict(int)
    
    with open("C:/Users/Rushikesh/Desktop/Data/Hackathon/Hack2Skill-RedRob/Hackathon-Details/candidates.jsonl", "r", encoding="utf-8") as f:
        for idx, line in enumerate(f):
            c = json.loads(line)
            cid = c["candidate_id"]
            
            # Check if honeypot or disqualified to skip parsing tfidf (helps speed up!)
            if is_honeypot(c, current_time):
                continue
            
            disq, disq_reason = check_disqualifications(c)
            if disq:
                continue
                
            prof = c["profile"]
            summary = prof.get("summary", "")
            headline = prof.get("headline", "")
            current_title = prof.get("current_title", "")
            skills_str = " ".join([s["name"] for s in c.get("skills", [])])
            
            combined_text = f"{current_title} {headline} {summary} {skills_str}"
            tokens = [w for w in tokenize(combined_text) if w not in stop_words]
            tf = collections.Counter(tokens)
            
            doc_tfs = (cid, tf)
            candidates.append((c, tf))
            cids.append(cid)
            
            for word in tf.keys():
                df[word] += 1
                
            if idx > 0 and idx % 20000 == 0:
                print(f"  Processed {idx} candidate texts...")
                
    N = len(candidates)
    print(f"Loaded {N} qualified candidates. Calculating IDF...")
    
    idf = {}
    for word, count in df.items():
        idf[word] = math.log(1.0 + (N / (1.0 + count)))
        
    # Calculate JD TF-IDF vector
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
    
    print("Layer 2: Scoring candidates...")
    scored_candidates = []
    
    # Calculate similarity scores
    raw_similarities = []
    for c, tf in candidates:
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
    print(f"Max Cosine Similarity: {max_sim:.4f}")
    
    # Score each candidate
    for i, (c, tf) in enumerate(candidates):
        cid = c["candidate_id"]
        sim = raw_similarities[i]
        
        # Normalize tfidf score to scale of 0-100
        tfidf_score = (sim / max_sim) * 100.0
        
        meta = calculate_meta_scores(c, current_time)
        
        # Base score (Hybrid Formula)
        base_score = (
            (0.20 * meta["title"]) + 
            (0.30 * tfidf_score) + 
            (0.20 * meta["concept_skill"]) + 
            (0.15 * meta["yoe"]) + 
            (0.08 * meta["edu"]) + 
            (0.07 * meta["loc"])
        )
        
        # Behavioral modifier
        behavioral_mult = get_behavioral_multiplier(c["redrob_signals"], current_time)
        final_score = base_score * behavioral_mult
        
        location = c["profile"].get("location", "").lower()
        is_pune_noida = "pune" in location or "noida" in location or "delhi ncr" in location or "ncr" in location
        notice = c["redrob_signals"].get("notice_period_days", 60)
        
        reasoning = generate_reasoning(c, c["profile"]["years_of_experience"], meta["matched_skills"], is_pune_noida, notice, c["redrob_signals"])
        
        scored_candidates.append((cid, final_score, reasoning, c))
        
    # Sort by score descending
    scored_candidates.sort(key=lambda x: x[1], reverse=True)
    
    print(f"Layer 3: Top 10 Hybrid Candidates:")
    for rank, (cid, score, reasoning, c) in enumerate(scored_candidates[:10], 1):
        print(f"  {rank}. {cid} | Score={score:.2f} | Title='{c['profile']['current_title']}' | YoE={c['profile']['years_of_experience']} | Loc={c['profile']['location']}")
        print(f"     Reasoning: {reasoning}")
        
    duration = time.time() - start_time
    print(f"Total pipeline execution time: {duration:.2f} seconds.")

if __name__ == "__main__":
    main()
