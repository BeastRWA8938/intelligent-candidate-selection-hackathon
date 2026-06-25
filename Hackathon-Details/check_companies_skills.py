import os
import json
import re

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def check_data():
    company_descriptions = {}
    expert_zero_duration_candidates = []
    total_candidates = 0
    
    # Let's read the first 10,000 candidates to keep it fast, or the whole file if it's quick.
    # The file candidates.jsonl is 487MB, which has 100,000 lines. Let's process the whole file, it should take ~10-15 seconds in Python.
    print("Scanning candidates.jsonl...")
    
    with open(os.path.join(PROJECT_ROOT, "Hackathon-Details", "candidates.jsonl"), "r", encoding="utf-8") as f:
        for idx, line in enumerate(f):
            total_candidates += 1
            c = json.loads(line)
            cid = c["candidate_id"]
            
            # Check skills
            expert_zero_skills = 0
            for s in c.get("skills", []):
                if s.get("proficiency") == "expert" and s.get("duration_months", 0) == 0:
                    expert_zero_skills += 1
            if expert_zero_skills >= 5:
                expert_zero_duration_candidates.append((cid, expert_zero_skills))
                
            # Collect company descriptions
            for job in c.get("career_history", []):
                comp = job.get("company", "").strip()
                desc = job.get("description", "")
                if comp:
                    if comp not in company_descriptions:
                        company_descriptions[comp] = []
                    # Keep unique descriptions or descriptions containing numbers/years
                    if len(company_descriptions[comp]) < 5:
                        company_descriptions[comp].append(desc)
                        
            if idx > 0 and idx % 20000 == 0:
                print(f"Processed {idx} candidates...")
                
    print(f"Total candidates scanned: {total_candidates}")
    print(f"Candidates with >=5 expert skills with 0 duration: {len(expert_zero_duration_candidates)}")
    if expert_zero_duration_candidates:
        print("Sample expert-zero candidates:", expert_zero_duration_candidates[:10])
        
    # Let's search company descriptions for founding year clues
    print("\nSearching company descriptions for founding year patterns...")
    founding_patterns = [
        re.compile(r"founded in (\d{4})", re.I),
        re.compile(r"established in (\d{4})", re.I),
        re.compile(r"started in (\d{4})", re.I),
        re.compile(r"founded (\d+) years ago", re.I),
        re.compile(r"startup founded in", re.I),
        re.compile(r"launch in (\d{4})", re.I),
        re.compile(r"launched in (\d{4})", re.I)
    ]
    
    founding_matches = []
    for comp, descs in company_descriptions.items():
        for desc in descs:
            for pat in founding_patterns:
                m = pat.search(desc)
                if m:
                    founding_matches.append((comp, desc, m.group(0)))
                    break
                    
    print(f"Found {len(founding_matches)} company descriptions with founding patterns.")
    for m in founding_matches[:10]:
        print(f"Company: {m[0]} -> Pattern Match: {m[2]}\n  Desc: {m[1][:200]}...")

if __name__ == "__main__":
    check_data()