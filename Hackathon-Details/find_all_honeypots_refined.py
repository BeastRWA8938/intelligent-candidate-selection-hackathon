import os
import json
from datetime import datetime

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def refine_scan():
    current_time = datetime(2026, 6, 18)
    
    anom_yoe_1 = 0
    anom_yoe_05 = 0
    anom_job_dur_6 = 0
    anom_job_dur_3 = 0
    
    expert_zero_1 = 0
    expert_zero_3 = 0
    expert_zero_5 = 0
    
    # Let's count how many candidates trigger each threshold
    with open(os.path.join(PROJECT_ROOT, "Hackathon-Details", "candidates.jsonl"), "r", encoding="utf-8") as f:
        for idx, line in enumerate(f):
            c = json.loads(line)
            yoe = c["profile"]["years_of_experience"]
            history = c["career_history"]
            
            # YoE checks
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
                if yoe > span_years + 1.0:
                    anom_yoe_1 += 1
                if yoe > span_years + 0.5:
                    anom_yoe_05 += 1
                    
            # Job duration checks
            job_dur_6 = False
            job_dur_3 = False
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
                        if dur > calc_dur + 6:
                            job_dur_6 = True
                        if dur > calc_dur + 3:
                            job_dur_3 = True
                    except:
                        pass
            if job_dur_6:
                anom_job_dur_6 += 1
            if job_dur_3:
                anom_job_dur_3 += 1
                
            # Expert zero checks
            expert_zero_skills = [s["name"] for s in c.get("skills", []) if s.get("proficiency") == "expert" and s.get("duration_months", 0) == 0]
            if len(expert_zero_skills) >= 1:
                expert_zero_1 += 1
            if len(expert_zero_skills) >= 3:
                expert_zero_3 += 1
            if len(expert_zero_skills) >= 5:
                expert_zero_5 += 1

    print(f"YoE > span + 1.0: {anom_yoe_1}")
    print(f"YoE > span + 0.5: {anom_yoe_05}")
    print(f"Job duration > calendar + 6m: {anom_job_dur_6}")
    print(f"Job duration > calendar + 3m: {anom_job_dur_3}")
    print(f"Expert zero skills >= 1: {expert_zero_1}")
    print(f"Expert zero skills >= 3: {expert_zero_3}")
    print(f"Expert zero skills >= 5: {expert_zero_5}")

if __name__ == "__main__":
    refine_scan()