import json
from datetime import datetime

def inspect_sample_candidates():
    with open("C:/Users/Rushikesh/Desktop/Data/Hackathon/Hack2Skill-RedRob/Hackathon-Details/sample_candidates.json", "r", encoding="utf-8") as f:
        candidates = json.load(f)
        
    print(f"Loaded {len(candidates)} sample candidates.")
    
    for c in candidates:
        cid = c["candidate_id"]
        yoe = c["profile"]["years_of_experience"]
        history = c["career_history"]
        
        # Calculate span of career history
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
                    
        current_time = datetime(2026, 6, 18) # Current local time from metadata
        
        if first_start:
            span_years = (current_time - first_start).days / 365.25
            # If years_of_experience is much larger than the span of time since they started their first job, it's impossible!
            if yoe > span_years + 0.5:
                print(f"Candidate {cid}: Inconsistent experience! YoE={yoe}, but first job started on {first_start.strftime('%Y-%m-%d')} (max span {span_years:.2f} years)")
                
        # Let's check if there are other anomalies:
        # Check if any job's duration_months matches the dates
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
                    # If duration_months is way off from dates
                    if abs(calc_dur - dur) > 12: # more than 1 year difference
                        print(f"Candidate {cid}: job date-duration discrepancy! Job={job['company']}, dates={sd} to {ed}, duration={dur} months, calculated={calc_dur:.1f} months")
                except Exception as e:
                    print(f"Err: {e}")

if __name__ == "__main__":
    inspect_sample_candidates()
