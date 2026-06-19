import json
from datetime import datetime

def search_more_anomalies():
    current_time = datetime(2026, 6, 18)
    
    edu_date_anomaly = 0
    active_before_signup = 0
    multiple_current_jobs = 0
    job_date_overlap_anomaly = 0
    
    with open("C:/Users/Rushikesh/Desktop/Data/Hackathon/Hack2Skill-RedRob/Hackathon-Details/candidates.jsonl", "r", encoding="utf-8") as f:
        for idx, line in enumerate(f):
            c = json.loads(line)
            cid = c["candidate_id"]
            
            # 1. Education date anomaly (start_year > end_year)
            for edu in c.get("education", []):
                sy = edu.get("start_year")
                ey = edu.get("end_year")
                if sy and ey and sy > ey:
                    edu_date_anomaly += 1
                    if edu_date_anomaly <= 5:
                        print(f"[{cid}] Edu anomaly: start={sy} > end={ey}")
            
            # 2. Activity before signup
            signals = c["redrob_signals"]
            su = signals.get("signup_date")
            la = signals.get("last_active_date")
            if su and la:
                try:
                    su_dt = datetime.strptime(su, "%Y-%m-%d")
                    la_dt = datetime.strptime(la, "%Y-%m-%d")
                    if la_dt < su_dt:
                        active_before_signup += 1
                        if active_before_signup <= 5:
                            print(f"[{cid}] Activity anomaly: signup={su} > last_active={la}")
                except:
                    pass
            
            # 3. Multiple current jobs
            current_jobs = 0
            for job in c.get("career_history", []):
                if job.get("is_current", False):
                    current_jobs += 1
            if current_jobs >= 2:
                multiple_current_jobs += 1
                
            # 4. Job date overlaps of large duration
            # If two jobs overlap and both are long duration, e.g., Job A is 2020-2024 and Job B is 2021-2025.
            # (In synthetic data, sometimes jobs are just randomized and overlap, but let's check).
            
    print(f"Edu anomalies: {edu_date_anomaly}")
    print(f"Active before signup: {active_before_signup}")
    print(f"Multiple current jobs: {multiple_current_jobs}")

if __name__ == "__main__":
    search_more_anomalies()
