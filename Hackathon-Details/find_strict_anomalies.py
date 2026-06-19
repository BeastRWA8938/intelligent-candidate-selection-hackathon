import json
from datetime import datetime

def test_rules():
    current_time = datetime(2026, 6, 18)
    
    anomalous_yoe_count = 0
    anomalous_job_dur_count = 0
    expert_zero_count = 0
    expert_zero_5_count = 0
    
    # Detailed counts for combinations
    rules_triggered = {}
    
    with open("C:/Users/Rushikesh/Desktop/Data/Hackathon/Hack2Skill-RedRob/Hackathon-Details/candidates.jsonl", "r", encoding="utf-8") as f:
        for idx, line in enumerate(f):
            c = json.loads(line)
            cid = c["candidate_id"]
            
            yoe = c["profile"]["years_of_experience"]
            history = c["career_history"]
            
            # 1. Check YoE anomaly
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
            
            yoe_anomaly = False
            if first_start:
                span_years = (current_time - first_start).days / 365.25
                if yoe > span_years + 0.5:
                    yoe_anomaly = True
                    anomalous_yoe_count += 1
            
            # 2. Check Job Duration anomaly
            job_dur_anomaly = False
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
                        if dur > calc_dur + 12: # stated duration exceeds calendar span by more than a year
                            job_dur_anomaly = True
                    except:
                        pass
            if job_dur_anomaly:
                anomalous_job_dur_count += 1
                
            # 3. Check Expert zero skills
            expert_zero_skills = [s["name"] for s in c.get("skills", []) if s.get("proficiency") == "expert" and s.get("duration_months", 0) == 0]
            if len(expert_zero_skills) >= 1:
                expert_zero_count += 1
            if len(expert_zero_skills) >= 5:
                expert_zero_5_count += 1
                
            # Check how they combine
            tup = (yoe_anomaly, job_dur_anomaly, len(expert_zero_skills) >= 5)
            if any(tup):
                rules_triggered[tup] = rules_triggered.get(tup, 0) + 1
                if len(rules_triggered) <= 20 and len(expert_zero_skills) >= 5:
                    pass

    print(f"YoE anomaly count: {anomalous_yoe_count}")
    print(f"Job duration anomaly count: {anomalous_job_dur_count}")
    print(f"Expert zero count (>=1 skill): {expert_zero_count}")
    print(f"Expert zero count (>=5 skills): {expert_zero_5_count}")
    print("\nCombinations of rules (YoE_anomaly, Job_dur_anomaly, Expert_zero_5):")
    for k, v in rules_triggered.items():
        print(f"  Rule combo {k}: {v} candidates")

if __name__ == "__main__":
    test_rules();
