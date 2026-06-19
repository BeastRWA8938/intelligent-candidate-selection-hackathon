import json

def check_salary():
    salary_honeypots = set()
    
    with open("C:/Users/Rushikesh/Desktop/Data/Hackathon/Hack2Skill-RedRob/Hackathon-Details/candidates.jsonl", "r", encoding="utf-8") as f:
        for idx, line in enumerate(f):
            c = json.loads(line)
            cid = c["candidate_id"]
            
            sal = c["redrob_signals"].get("expected_salary_range_inr_lpa", {})
            s_min = sal.get("min")
            s_max = sal.get("max")
            if s_min is not None and s_max is not None and s_min > s_max:
                salary_honeypots.add(cid)
                
    # Load previously flagged honeypots
    file_path = "C:/Users/Rushikesh/Desktop/Data/Hackathon/Hack2Skill-RedRob/scratch/flagged_candidates.json"
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    existing_honeypots = set(data["honeypot"])
    
    print(f"Honeypots found via salary logic: {len(salary_honeypots)}")
    print(f"Are they already in the existing honeypots? {salary_honeypots.issubset(existing_honeypots)}")
    extra = salary_honeypots - existing_honeypots
    print(f"Extra honeypots found: {len(extra)}")
    if extra:
        print(f"Extra IDs: {sorted(list(extra))}")

if __name__ == "__main__":
    check_salary()
