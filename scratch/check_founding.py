import json
import re
from datetime import datetime

def check_founding():
    current_time = datetime(2026, 6, 18)
    founding_honeypots = set()
    
    with open("C:/Users/Rushikesh/Desktop/Data/Hackathon/Hack2Skill-RedRob/Hackathon-Details/candidates.jsonl", "r", encoding="utf-8") as f:
        for idx, line in enumerate(f):
            c = json.loads(line)
            cid = c["candidate_id"]
            
            founding_anomaly = False
            for job in c.get("career_history", []):
                desc = job.get("description", "")
                company = job.get("company", "")
                start_date_str = job.get("start_date")
                
                # Check for "founded in YYYY"
                match = re.search(r"founded in (\d{4})", desc, re.IGNORECASE)
                if match:
                    founding_year = int(match.group(1))
                    if start_date_str:
                        start_year = int(start_date_str.split("-")[0])
                        if start_year < founding_year:
                            founding_anomaly = True
                
                # Check for "founded Y years ago"
                match_ago = re.search(r"founded (\d+)\s+years?\s+ago", desc, re.IGNORECASE)
                if match_ago:
                    years_ago = int(match_ago.group(1))
                    founding_year = 2026 - years_ago
                    if start_date_str:
                        start_year = int(start_date_str.split("-")[0])
                        if start_year < founding_year:
                            founding_anomaly = True
                            
            if founding_anomaly:
                founding_honeypots.add(cid)
                
    # Load previously flagged honeypots
    file_path = "C:/Users/Rushikesh/Desktop/Data/Hackathon/Hack2Skill-RedRob/scratch/flagged_candidates.json"
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    existing_honeypots = set(data["honeypot"])
    
    print(f"Honeypots found via company founding logic: {len(founding_honeypots)}")
    print(f"Are they already in the existing honeypots? {founding_honeypots.issubset(existing_honeypots)}")
    extra = founding_honeypots - existing_honeypots
    print(f"Extra honeypots found: {len(extra)}")
    if extra:
        print(f"Extra IDs: {sorted(list(extra))}")

if __name__ == "__main__":
    check_founding()
