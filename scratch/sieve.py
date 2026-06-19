import json
import re
from datetime import datetime

# Consulting companies list as specified in the hackathon details
CONSULTING_COMPANIES = {
    "tcs", "tata consultancy services", "infosys", "wipro", "accenture", 
    "cognizant", "capgemini", "hcl", "tech mahindra", "l&t", "lnt", 
    "mindtree", "mphasis", "ust global", "hexaware"
}

# Disqualified titles for trap candidates
BAD_TITLES = {
    "graphic designer", "mechanical engineer", "operations manager", "marketing manager",
    "accountant", "sales executive", "hr specialist", "customer support",
    "financial analyst", "content writer", "product manager", "ux designer", "ui designer",
    "marketing specialist", "recruiter", "sales manager", "business development manager"
}

def is_honeypot(candidate, current_time=datetime(2026, 6, 18), yoe_threshold=0.5, dur_threshold=3.0, expert_zero_threshold=1):
    """
    Identifies if a candidate is a honeypot based on date-duration logic and expert zero-duration skills.
    
    Returns:
        bool: True if honeypot, False otherwise.
        dict: Breakdown of which rules were triggered.
    """
    triggers = {
        "yoe_mismatch": False,
        "job_duration_mismatch": False,
        "expert_zero_duration": False
    }
    
    yoe = candidate.get("profile", {}).get("years_of_experience", 0)
    history = candidate.get("career_history", [])
    
    # Rule 1: YoE vs First Job Start Date
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
        if yoe > span_years + yoe_threshold:
            triggers["yoe_mismatch"] = True
            
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
                if dur > calc_dur + dur_threshold:
                    triggers["job_duration_mismatch"] = True
                    break
            except:
                pass
                
    # Rule 3: Expert skills with 0 duration
    expert_zero_skills = [
        s["name"] for s in candidate.get("skills", []) 
        if s.get("proficiency") == "expert" and s.get("duration_months", 0) == 0
    ]
    if len(expert_zero_skills) >= expert_zero_threshold:
        triggers["expert_zero_duration"] = True
        
    is_hp = any(triggers.values())
    return is_hp, triggers

def is_disqualified(candidate):
    """
    Checks if a candidate is disqualified due to bad titles or consulting-firm-only history.
    
    Returns:
        bool: True if disqualified, False otherwise.
        dict: Breakdown of which disqualifications were triggered.
    """
    triggers = {
        "bad_title": False,
        "consulting_only": False
    }
    
    # Check 1: Current Title Disqualification (exact match or in list)
    curr_title = candidate.get("profile", {}).get("current_title", "").lower().strip()
    if curr_title in BAD_TITLES:
        triggers["bad_title"] = True
        
    # Check 2: Consulting Firms only Disqualification
    history = candidate.get("career_history", [])
    if history:
        all_consulting = True
        for job in history:
            comp = job.get("company", "").lower().strip()
            # If the company doesn't contain any consulting firm substring, then not all consulting
            is_consulting = any(cs in comp for cs in CONSULTING_COMPANIES)
            if not is_consulting:
                all_consulting = False
                break
        if all_consulting:
            triggers["consulting_only"] = True
            
    is_dq = any(triggers.values())
    return is_dq, triggers
