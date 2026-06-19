import json
import time
import math
import collections
import re
import argparse
import csv
import heapq
import logging
from datetime import datetime

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("Ranker")

# Consulting companies set (matched with word boundaries)
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

# Key phrases to normalize and map to single tokens
KEY_PHRASES = {
    "machine learning": "machine_learning",
    "vector search": "vector_search",
    "hybrid search": "hybrid_search",
    "dense retrieval": "dense_retrieval",
    "vector database": "vector_database",
    "vector databases": "vector_database",
    "sentence transformers": "sentence_transformers",
    "sentence-transformers": "sentence_transformers",
    "information retrieval": "information_retrieval",
    "learning to rank": "learning_to_rank",
    "fine tuning": "fine_tuning",
    "fine-tuning": "fine_tuning",
    "open source": "open_source",
    "open-source": "open_source",
    "ab testing": "ab_testing",
    "a/b testing": "ab_testing",
    "vector dbs": "vector_database",
    "large language models": "llm",
    "large language model": "llm"
}

# Concept Clusters for robust skill matching (using compound normalized tokens)
CONCEPT_CLUSTERS = {
    "retrieval_search": {
        "embeddings", "retrieval", "dense_retrieval", "hybrid_search", 
        "vector_search", "information_retrieval", "search", "elasticsearch", 
        "opensearch", "bm25"
    },
    "vector_dbs": {
        "pinecone", "weaviate", "qdrant", "milvus", "faiss", "chroma", "vector_database"
    },
    "models_frameworks": {
        "sentence_transformers", "bert", "transformers", "pytorch", "tensorflow", 
        "huggingface", "llm", "llms", "gans", "yolo", "diffusion models", "rag", "fine_tuning"
    },
    "evaluation": {
        "ndcg", "mrr", "map", "evaluation", "offline evaluation", "ab_testing"
    }
}

def tokenize(text):
    # Matches words with letters, numbers, plus signs, hashes, hyphens, and underscores
    # Examples: sentence-transformers, c++, c#, gpt-4, llama-3, e5, python
    tokens = re.findall(r"[a-z0-9_+#\-]+", text.lower())
    cleaned = []
    for t in tokens:
        t = t.strip("-")
        if not t:
            continue
        # Exclude pure numbers
        if t.isdigit():
            continue
        cleaned.append(t)
    return cleaned

def preprocess_text(text):
    text = text.lower()
    for phrase, replacement in KEY_PHRASES.items():
        text = text.replace(phrase, replacement)
    return text

def normalize_skill(name):
    if not name:
        return ""
    name = name.lower().strip()
    for phrase, replacement in KEY_PHRASES.items():
        if phrase in name:
            name = name.replace(phrase, replacement)
    # Strip database/library/framework qualifiers for soft matching
    name = name.replace(" db", "").replace(" database", "").replace(" framework", "").replace(" library", "")
    return name.strip()

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

def parse_date(date_str, current_time):
    if not date_str:
        return None
    date_str = str(date_str).strip()
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%Y-%m", "%Y"):
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    # Year-only regex fallback
    year_match = re.search(r"\b(19\d\d|20\d\d)\b", date_str)
    if year_match:
        try:
            return datetime(int(year_match.group(1)), 1, 1)
        except:
            pass
    return None

def is_honeypot(c, current_time):
    # Rule 1: YoE vs First Job Start Date
    yoe = c.get("profile", {}).get("years_of_experience")
    if yoe is None or not isinstance(yoe, (int, float)):
        yoe = 0.0
    yoe = float(yoe)
    
    history = c.get("career_history", [])
    first_start = None
    for job in history:
        sd = job.get("start_date")
        if sd:
            s_dt = parse_date(sd, current_time)
            if s_dt:
                if first_start is None or s_dt < first_start:
                    first_start = s_dt
                    
    if first_start:
        span_years = (current_time - first_start).days / 365.25
        # Relaxed buffer to 2.0 years to prevent false positives from rounded YoE/freelance
        if yoe > span_years + 2.0:
            return True
            
    # Rule 2: Job duration stated vs calendar span
    for job in history:
        sd = job.get("start_date")
        ed = job.get("end_date")
        dur = job.get("duration_months")
        if dur is None or not isinstance(dur, (int, float)):
            dur = 0.0
        dur = float(dur)
        
        if sd:
            s_dt = parse_date(sd, current_time)
            if s_dt:
                if ed:
                    e_dt = parse_date(ed, current_time)
                else:
                    e_dt = current_time
                if e_dt:
                    calc_dur = (e_dt - s_dt).days / 30.4
                    if dur > calc_dur + 3.0:
                        return True
                        
    # Rule 3: Expert skills with 0 duration (relaxed threshold to >= 4 to protect recall)
    expert_zero_skills = []
    for s in c.get("skills", []):
        prof_level = s.get("proficiency")
        if isinstance(prof_level, str) and prof_level.lower().strip() == "expert":
            dur = s.get("duration_months", 0)
            if dur is None or dur == 0:
                expert_zero_skills.append(s.get("name", ""))
                
    if len(expert_zero_skills) >= 4:
        return True

    return False


def is_consulting_company(company_name):
    if not company_name:
        return False
    company_name = company_name.lower().strip()
    for cs in CONSULTING_COMPANIES:
        pattern = rf"\b{re.escape(cs)}\b"
        if re.search(pattern, company_name) or company_name == cs:
            return True
    return False

def is_disqualified_title(title):
    if not title:
        return False
    title = title.lower().strip()
    for bt in BAD_TITLES:
        pattern = rf"\b{re.escape(bt)}\b"
        if re.search(pattern, title) or title == bt:
            return True
    # Disqualify HR/Recruiter hybrid roles that list engineering terms in profile summaries
    hr_terms = {"recruiter", "talent acquisition", "hr specialist", "human resources", "headhunter", "sourcer"}
    if any(term in title for term in hr_terms) and not any(eng in title for eng in ["engineer", "developer", "architect"]):
        return True
    return False

def check_disqualifications(c):
    prof = c.get("profile", {})
    curr_title = prof.get("current_title")
    if curr_title is None or not isinstance(curr_title, str):
        curr_title = ""
    curr_title = curr_title.lower().strip()
    
    # 1. Bad Title
    if is_disqualified_title(curr_title):
        return True, "Irrelevant current title"
        
    # 2. Consulting firm only
    history = c.get("career_history", [])
    if not history:
        return False, ""
        
    all_consulting = True
    for job in history:
        comp = job.get("company")
        if comp is None or not isinstance(comp, str):
            comp = ""
        comp = comp.lower().strip()
        if not comp:
            continue
        if not is_consulting_company(comp):
            all_consulting = False
            break
            
    if all_consulting:
        return True, "Only worked at consulting/services firms"
        
    return False, ""

def calculate_meta_scores(c, weights, current_time):
    prof = c.get("profile", {})
    curr_title = prof.get("current_title")
    if curr_title is None or not isinstance(curr_title, str):
        curr_title = ""
    curr_title = curr_title.lower().strip()
    
    yoe = prof.get("years_of_experience")
    if yoe is None or not isinstance(yoe, (int, float)):
        yoe = 0.0
    yoe = float(yoe)
    
    location = prof.get("location")
    if location is None or not isinstance(location, str):
        location = ""
    location = location.lower().strip()
    
    signals = c.get("redrob_signals", {})
    skills = c.get("skills", [])
    skill_names_set = {normalize_skill(s.get("name", "")) for s in skills if s.get("name")}
    
    # 1. Title Score (avoiding substring match bugs)
    title_score = 20.0
    # Guard against hybrid recruiter/engineer titles
    if not is_disqualified_title(curr_title):
        if any(gt in curr_title for gt in GOOD_TITLES):
            title_score = 100.0
        elif "engineer" in curr_title or "developer" in curr_title or "programmer" in curr_title or "architect" in curr_title:
            title_score = 60.0
            
    # 2. Concept Skill Score (using normalized soft match clusters)
    matched_clusters = 0
    skills_weighted = 0.0
    matched_skills = []
    
    for cluster_name, keywords in CONCEPT_CLUSTERS.items():
        overlap = skill_names_set.intersection(keywords)
        if overlap:
            matched_clusters += 1
            for s in skills:
                s_name = s.get("name", "")
                norm_s = normalize_skill(s_name)
                if norm_s in overlap:
                    prof_level = s.get("proficiency", "beginner")
                    if not isinstance(prof_level, str):
                        prof_level = "beginner"
                    prof_level = prof_level.lower().strip()
                    prof_mult = {"beginner": 0.5, "intermediate": 0.8, "advanced": 1.0, "expert": 1.2}.get(prof_level, 0.5)
                    
                    dur = s.get("duration_months")
                    if dur is None or not isinstance(dur, (int, float)):
                        dur = 0.0
                    dur = float(dur)
                    
                    end = s.get("endorsements")
                    if end is None or not isinstance(end, (int, float)):
                        end = 0.0
                    end = float(end)
                    end_mult = min(1.5, 1.0 + (end / 50.0))
                    
                    s_score = 10.0 * prof_mult * end_mult * (min(36.0, dur) / 12.0)
                    skills_weighted += s_score
                    matched_skills.append(s_name)
                    
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
        if not isinstance(tier, str):
            tier = "unknown"
        tier = tier.lower().strip()
        if tier == "tier_1":
            edu_score = max(edu_score, 100.0)
        elif tier == "tier_2":
            edu_score = max(edu_score, 80.0)
            
    # 5. Location Score (fixing Jaipur relocation bug)
    loc_score = 30.0
    is_pune_noida = "pune" in location or "noida" in location or "delhi ncr" in location or "ncr" in location
    is_tier1_india = any(city in location for city in ["hyderabad", "mumbai", "bangalore", "bengaluru", "chennai"])
    
    if is_pune_noida:
        loc_score = 100.0
    elif is_tier1_india and signals.get("willing_to_relocate", False):
        loc_score = 85.0
    elif is_tier1_india:
        loc_score = 60.0
    elif signals.get("willing_to_relocate", False):
        loc_score = 70.0 # Reward relocation willingness for non-tier1
        
    return {
        "title": title_score,
        "concept_skill": concept_skill_score,
        "yoe": yoe_score,
        "edu": edu_score,
        "loc": loc_score,
        "matched_skills": matched_skills
    }

def get_behavioral_multiplier(signals, current_time):
    # Recruiter Response Rate
    resp_rate = signals.get("recruiter_response_rate")
    if resp_rate is None or not isinstance(resp_rate, (int, float)):
        resp_rate = 0.5
    # Moderate multiplier swing (was 0.7-1.3, now 0.9-1.1)
    resp_mult = 0.9 + (resp_rate * 0.2)
    
    # Platform Activity
    last_act = signals.get("last_active_date")
    act_mult = 1.0
    if last_act:
        la_dt = parse_date(last_act, current_time)
        if la_dt:
            days_inactive = (current_time - la_dt).days
            if days_inactive <= 30:
                act_mult = 1.1 # was 1.2
            elif days_inactive <= 90:
                act_mult = 1.0
            elif days_inactive <= 180:
                act_mult = 0.95 # was 0.8
            else:
                act_mult = 0.85 # was 0.4
                
    # Notice Period
    notice = signals.get("notice_period_days")
    if notice is None or not isinstance(notice, (int, float)):
        notice = 60
    # Moderate multiplier range (was 0.5-1.15, now 0.85-1.1)
    if notice <= 30:
        notice_mult = 1.1
    elif notice <= 60:
        notice_mult = 1.0
    elif notice <= 90:
        notice_mult = 0.9
    else:
        notice_mult = 0.85
        
    # Open to Work
    otw = signals.get("open_to_work_flag", False)
    otw_mult = 1.05 if otw else 0.98
    
    # GitHub Activity
    gh_score = signals.get("github_activity_score")
    if gh_score is None or not isinstance(gh_score, (int, float)):
        gh_score = -1
        
    if gh_score >= 50:
        gh_mult = 1.05
    elif gh_score >= 10:
        gh_mult = 1.0
    else:
        gh_mult = 0.98
        
    return {
        "composite": resp_mult * act_mult * notice_mult * otw_mult * gh_mult,
        "breakdown": {
            "response_mult": resp_mult,
            "activity_mult": act_mult,
            "notice_mult": notice_mult,
            "open_to_work_mult": otw_mult,
            "github_mult": gh_mult
        }
    }

def generate_reasoning(c, yoe, matched_skills, is_pune_noida, notice, signals, rank=None):
    cid = c.get("candidate_id", "CAND_0000000")
    seed = sum(ord(char) for char in cid)
    
    prof = c.get("profile", {})
    current_title = prof.get("current_title", "Engineer")
    current_company = prof.get("current_company", "Company")
    location = prof.get("location", "India")
    resp_rate = signals.get("recruiter_response_rate", 0.5)
    
    # 1. Experience & Title Statement (checking yoe defensively)
    if yoe >= 8.0:
        yoe_desc = "highly experienced expert"
    elif yoe >= 5.0:
        yoe_desc = "senior backend/ML engineer"
    elif yoe >= 3.0:
        yoe_desc = "backend/ML professional"
    else:
        yoe_desc = "growing backend/ML developer"
        
    exp_templates = [
        f"A {yoe_desc} offering {yoe:.1f} years of experience, presently working as {current_title} at {current_company}.",
        f"Brings {yoe:.1f} years of industry experience as a {yoe_desc}, currently holding the role of {current_title} with {current_company}.",
        f"Demonstrates {yoe:.1f} years of experience, currently active as a {yoe_desc} ({current_title}) at {current_company}."
    ]
    part1 = exp_templates[seed % len(exp_templates)]
    
    # 2. Skills and JD Fit (no hardcoded "advanced machine learning" fallback if candidate has other skills)
    if matched_skills:
        skills_str = ", ".join(matched_skills[:2])
    else:
        # Use top skills listed in profile if concept clusters are empty
        candidate_skills = [s.get("name") for s in c.get("skills", []) if s.get("name")]
        if candidate_skills:
            skills_str = ", ".join(candidate_skills[:2])
        else:
            skills_str = "software development"
            
    nice_to_haves = []
    skills_lower = [s.get("name", "").lower() for s in c.get("skills", [])]
    skills_str_all = "".join(skills_lower)
    if any(k in skills_str_all for k in ["fine-tuning", "lora", "peft", "qlora"]):
        nice_to_haves.append("LLM fine-tuning")
    if any(k in skills_str_all for k in ["xgboost", "lightgbm", "learning to rank", "ltr"]):
        nice_to_haves.append("learning-to-rank models")
    if any(k in skills_str_all for k in ["distributed", "spark", "hadoop", "scale"]):
        nice_to_haves.append("distributed search scaling")
        
    nth_str = ""
    if nice_to_haves:
        nth_str = f" and experience in {nice_to_haves[0]}"
        
    # Fit statements based on rank
    if rank is not None:
        if rank <= 10:
            fit_templates = [
                f"They demonstrate outstanding technical command over {skills_str}{nth_str}, making them a top-tier fit for the founding team.",
                f"Displays exceptional hands-on expertise in {skills_str}{nth_str}, aligning perfectly with our core technical needs.",
                f"An excellent fit for the founding role, showcasing deep proficiency in {skills_str}{nth_str}."
            ]
        elif rank <= 50:
            fit_templates = [
                f"Strong match for the JD, showcasing solid skills in {skills_str}{nth_str}.",
                f"Highly skilled in {skills_str}{nth_str}, aligning well with our technical stack.",
                f"Demonstrates strong hands-on capabilities in {skills_str}{nth_str}."
            ]
        else:
            fit_templates = [
                f"A viable candidate with relevant skills in {skills_str}{nth_str}.",
                f"Demonstrates capability in {skills_str}{nth_str}, with potential for this role.",
                f"Showcases decent alignment with the technical requirements, offering {skills_str}{nth_str}."
            ]
    else:
        fit_templates = [
            f"They demonstrate deep technical command over {skills_str}{nth_str}.",
            f"Strong match for the JD, showcasing skills in {skills_str}{nth_str}.",
            f"Displays hands-on expertise in {skills_str}{nth_str}."
        ]
    part2 = fit_templates[(seed // 3) % len(fit_templates)]
    
    # 3. Location phrasing
    loc_templates_noida_pune = [
        "Positioned in the Pune/Noida region, allowing for immediate hybrid onboarding.",
        "Located in target office location (Pune/Noida), meeting the hybrid setup needs.",
        "Based locally in Pune/Noida, perfect for our current office cadence."
    ]
    loc_templates_relocate = [
        f"Willing to relocate to Noida/Pune from {location}.",
        f"Open to relocating from {location} to Noida/Pune office.",
        f"Based in {location} but willing to relocate to target office."
    ]
    loc_templates_other = [
        f"Currently located in {location}.",
        f"Based out of {location}.",
        f"Operating from {location}."
    ]
    
    if is_pune_noida:
        part3 = loc_templates_noida_pune[(seed // 7) % len(loc_templates_noida_pune)]
    elif signals.get("willing_to_relocate", False):
        part3 = loc_templates_relocate[(seed // 7) % len(loc_templates_relocate)]
    else:
        part3 = loc_templates_other[(seed // 7) % len(loc_templates_other)]
        
    # 4. Engagement, Notice Period, and Concerns
    concerns = []
    if notice >= 90:
        concerns.append(f"notice period of {notice} days is longer than preferred")
    if resp_rate < 0.35:
        concerns.append(f"low response rate of {int(resp_rate*100)}% indicates poor availability")
    
    if concerns:
        concern_desc = " though " + " and ".join(concerns)
    else:
        concern_desc = ""
        
    active_templates = [
        f"Strong platform engagement with a {int(resp_rate*100)}% response rate.",
        f"Very active candidate showing a {int(resp_rate*100)}% recruiter response rate.",
        f"Excellent availability signals and a {int(resp_rate*100)}% response rate."
    ]
    active_str = active_templates[(seed // 11) % len(active_templates)]
    
    if concern_desc:
        part4 = f"Active on the platform{concern_desc}."
    else:
        part4 = f"{active_str} Stated notice period is {notice} days."
        
    styles = [
        f"{part1} {part2} {part3} {part4}",
        f"{part2} {part1} {part3} {part4}",
        f"{part1} {part3} {part2} {part4}"
    ]
    reasoning = styles[seed % len(styles)]
    return reasoning

class CandidateHeapItem:
    def __init__(self, score, candidate_id, c, meta, behavioral):
        self.score = score
        self.candidate_id = candidate_id
        self.c = c
        self.meta = meta
        self.behavioral = behavioral

    def __lt__(self, other):
        # Min-heap comparison (keeps worst candidates at the top)
        if math.isclose(self.score, other.score, abs_tol=1e-9):
            # Equal score: alphabetically larger candidate_id is "smaller" (worse)
            return self.candidate_id > other.candidate_id
        return self.score < other.score

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidates", default="./Hackathon-Details/candidates.jsonl", help="Path to candidates.jsonl")
    parser.add_argument("--out", default="./submission.csv", help="Path to output CSV file")
    args = parser.parse_args()
    
    start_time = time.time()
    current_time = datetime(2026, 6, 18)
    
    stop_words = get_stop_words()
    
    # Target Job Description Text
    jd_text = """
    Senior AI Engineer — Founding Team. Modern ML systems, embeddings, retrieval, ranking, LLMs, fine-tuning.
    embeddings-based retrieval systems (sentence-transformers, OpenAI embeddings, BGE, E5, or similar).
    vector databases or hybrid search infrastructure — Pinecone, Weaviate, Qdrant, Milvus, OpenSearch, Elasticsearch, FAISS.
    designing evaluation frameworks for ranking systems — NDCG, MRR, MAP.
    Strong Python.
    """
    jd_processed = preprocess_text(jd_text)
    jd_tokens = [w for w in tokenize(jd_processed) if w not in stop_words]
    jd_tf = collections.Counter(jd_tokens)
    
    # Pass 1: Stream candidates to compute Document Frequencies (DF)
    logger.info("Pass 1: Computing Document Frequencies and filtering anomalies...")
    df = collections.defaultdict(int)
    N = 0
    filtered_honeypot = 0
    filtered_disq = 0
    
    p1_start = time.time()
    with open(args.candidates, "r", encoding="utf-8") as f:
        for idx, line in enumerate(f):
            if idx > 0 and idx % 25000 == 0:
                logger.info(f"  Processed {idx} profiles in Pass 1...")
            c = json.loads(line)
            
            # Apply sieves early
            if is_honeypot(c, current_time):
                filtered_honeypot += 1
                continue
            disq, _ = check_disqualifications(c)
            if disq:
                filtered_disq += 1
                continue
                
            N += 1
            prof = c.get("profile", {})
            summary = prof.get("summary") or ""
            headline = prof.get("headline") or ""
            curr_title = prof.get("current_title") or ""
            skills_str = " ".join([s.get("name", "") for s in c.get("skills", []) if s.get("name")])
            
            combined_text = f"{curr_title} {headline} {summary} {skills_str}"
            processed_text = preprocess_text(combined_text)
            tokens = [w for w in tokenize(processed_text) if w not in stop_words]
            
            for word in set(tokens):
                df[word] += 1
                
    logger.info(f"Pass 1 complete in {time.time() - p1_start:.2f}s.")
    logger.info(f"Total candidates: {idx + 1}")
    logger.info(f"Filtered Honeypots: {filtered_honeypot}")
    logger.info(f"Filtered Disqualifications: {filtered_disq}")
    logger.info(f"Qualified candidates: {N}")
    
    if N == 0:
        logger.error("No qualified candidates left after screening!")
        return

    # Compute IDF map
    idf = {}
    for word, count in df.items():
        idf[word] = math.log(1.0 + (N / (1.0 + count)))
        
    # Build JD TF-IDF vector
    jd_vector = {}
    jd_norm = 0.0
    for word, tf_val in jd_tf.items():
        if word in idf:
            weight = tf_val * idf[word]
            jd_vector[word] = weight
            jd_norm += weight * weight
    jd_norm = math.sqrt(jd_norm)

    # Pass 2: Stream again to compute raw similarities and find max_sim
    logger.info("Pass 2: Calculating TF-IDF similarities and finding max similarity...")
    p2_start = time.time()
    raw_sims = {}
    max_sim = 0.0
    
    with open(args.candidates, "r", encoding="utf-8") as f:
        for idx, line in enumerate(f):
            if idx > 0 and idx % 25000 == 0:
                logger.info(f"  Processed {idx} profiles in Pass 2...")
            c = json.loads(line)
            cid = c["candidate_id"]
            
            # Apply sieves (identical logic)
            if is_honeypot(c, current_time) or check_disqualifications(c)[0]:
                continue
                
            # Tokenize and compute similarity
            prof = c.get("profile", {})
            summary = prof.get("summary") or ""
            headline = prof.get("headline") or ""
            curr_title = prof.get("current_title") or ""
            skills_str = " ".join([s.get("name", "") for s in c.get("skills", []) if s.get("name")])
            
            combined_text = f"{curr_title} {headline} {summary} {skills_str}"
            processed_text = preprocess_text(combined_text)
            tokens = [w for w in tokenize(processed_text) if w not in stop_words]
            tf = collections.Counter(tokens)
            
            dot_product = 0.0
            doc_norm = 0.0
            for word, tf_val in tf.items():
                weight = tf_val * idf.get(word, 0.0)
                doc_norm += weight * weight
                if word in jd_vector:
                    dot_product += weight * jd_vector[word]
            doc_norm = math.sqrt(doc_norm)
            
            sim = 0.0
            if doc_norm > 0.0 and jd_norm > 0.0:
                sim = dot_product / (doc_norm * jd_norm)
                
            raw_sims[cid] = sim
            if sim > max_sim:
                max_sim = sim
                
    logger.info(f"Pass 2 complete in {time.time() - p2_start:.2f}s. Max Similarity: {max_sim:.4f}")
    if max_sim == 0.0:
        max_sim = 1.0

    # Default weights for composite scoring
    weights = {
        "title": 0.20,
        "tfidf": 0.30,
        "concept_skill": 0.20,
        "yoe": 0.15,
        "edu": 0.08,
        "loc": 0.07
    }

    # Pass 3: Stream and score candidates on-the-fly, keeping top 100 in min-heap
    logger.info("Pass 3: Computing final scores and filtering top 100 candidates...")
    p3_start = time.time()
    top_heap = []
    
    with open(args.candidates, "r", encoding="utf-8") as f:
        for idx, line in enumerate(f):
            if idx > 0 and idx % 25000 == 0:
                logger.info(f"  Processed {idx} profiles in Pass 3...")
            c = json.loads(line)
            cid = c["candidate_id"]
            
            # Skip filtered
            if cid not in raw_sims:
                continue
                
            sim = raw_sims[cid]
            tfidf_score = (sim / max_sim) * 100.0
            
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
            
            item = CandidateHeapItem(final_score, cid, c, meta, behavioral)
            
            if len(top_heap) < 100:
                heapq.heappush(top_heap, item)
            else:
                if item > top_heap[0]:
                    heapq.heappushpop(top_heap, item)
                    
    logger.info(f"Pass 3 complete in {time.time() - p3_start:.2f}s.")
    
    # Pop items to get worst-to-best order, then reverse to get best-to-worst
    ordered_items = []
    while top_heap:
        ordered_items.append(heapq.heappop(top_heap))
    ordered_items.reverse()
    
    # Generate reasoning only for the final top 100 candidates (huge speed-up and rank-consistent reasoning)
    logger.info("Generating rank-consistent reasons for top 100 candidates...")
    final_top_100 = []
    for rank, item in enumerate(ordered_items, 1):
        c = item.c
        location = c["profile"].get("location", "").lower()
        is_pune_noida = "pune" in location or "noida" in location or "delhi ncr" in location or "ncr" in location
        notice = c["redrob_signals"].get("notice_period_days", 60)
        
        reasoning = generate_reasoning(
            c=c,
            yoe=c["profile"].get("years_of_experience", 0.0),
            matched_skills=item.meta["matched_skills"],
            is_pune_noida=is_pune_noida,
            notice=notice,
            signals=c["redrob_signals"],
            rank=rank
        )
        final_top_100.append((item.candidate_id, rank, item.score, reasoning))

    # Write top 100 results to CSV
    logger.info(f"Writing results to {args.out}...")
    with open(args.out, "w", encoding="utf-8", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["candidate_id", "rank", "score", "reasoning"])
        for cid, rank, score, reasoning in final_top_100:
            writer.writerow([cid, rank, f"{score:.3f}", reasoning])
            
    logger.info(f"All done! Pipeline completed successfully in {time.time() - start_time:.2f} seconds.")

if __name__ == "__main__":
    main()
