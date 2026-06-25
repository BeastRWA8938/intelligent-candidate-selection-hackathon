import os
import json
from datetime import datetime

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def check_union():
    current_time = datetime(2026, 6, 18)
    honeypots = set()
    
    with open(os.path.join(PROJECT_ROOT, "Hackathon-Details", "candidates.jsonl"), "r", encoding="utf-8") as f:
        for idx, line in enumerate(f):
            c = json.loads(line)
            cid = c["candidate_id"]
            
            is_anomaly = False
            
            # 1. YoE anomaly
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
                    is_anomaly = True
            
            # 2. Job duration anomaly
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
                            is_anomaly = True
                    except:
                        pass
            
            # 3. Expert zero skills
            expert_zero_skills = [s["name"] for s in c.get("skills", []) if s.get("proficiency") == "expert" and s.get("duration_months", 0) == 0]
            if len(expert_zero_skills) >= 1:
                is_anomaly = True
                
            if is_anomaly:
                honeypots.add(cid)
                
    print(f"Total unique honeypot candidates identified: {len(honeypots)}")
    print(f"Sample honeypot IDs: {list(honeypots)[:20]}")

if __name__ == "__main__":
    check_union()