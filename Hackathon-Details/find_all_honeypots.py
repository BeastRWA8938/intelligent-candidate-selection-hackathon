import json
from datetime import datetime

def find_honeypots():
    honeypots = []
    
    current_time = datetime(2026, 6, 18)
    
    with open("C:/Users/Rushikesh/Desktop/Data/Hackathon/Hack2Skill-RedRob/Hackathon-Details/candidates.jsonl", "r", encoding="utf-8") as f:
        for idx, line in enumerate(f):
            c = json.loads(line)
            cid = c["candidate_id"]
            
            reasons = []
            
            # Rule 1: Min Salary > Max Salary
            sal = c["redrob_signals"].get("expected_salary_range_inr_lpa", {})
            s_min = sal.get("min")
            s_max = sal.get("max")
            if s_min is not None and s_max is not None and s_min > s_max:
                reasons.append(f"Min salary ({s_min}) > Max salary ({s_max})")
                
            # Rule 2: Expert skills with 0 duration
            expert_zero_skills = [s["name"] for s in c.get("skills", []) if s.get("proficiency") == "expert" and s.get("duration_months", 0) == 0]
            if len(expert_zero_skills) >= 4:
                reasons.append(f"Expert in {len(expert_zero_skills)} skills with 0 duration: {expert_zero_skills}")
                
            # Rule 3: Stated Job Duration is impossible given calendar dates
            # E.g., starting in 2023 but stated duration is 100+ months
            for job in c.get("career_history", []):
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
                        # If duration stated is larger than calendar dates by more than 12 months
                        if dur > calc_dur + 12:
                            reasons.append(f"Job at {job['company']} started {sd} (calendar span {calc_dur:.1f}m) but stated duration is {dur}m")
                    except:
                        pass
            
            # Rule 4: YoE vs first job start date
            history = c["career_history"]
            yoe = c["profile"]["years_of_experience"]
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
                if yoe > span_years + 2.0:
                    reasons.append(f"YoE is {yoe} but first job started in {first_start.strftime('%Y-%m-%d')} (span {span_years:.2f} years)")
                    
            if reasons:
                honeypots.append((cid, reasons))
                
    print(f"Total honeypots found: {len(honeypots)}")
    for hp in honeypots[:15]:
        print(f"Honeypot: {hp[0]}")
        for r in hp[1]:
            print(f"  - {r}")
        print()

if __name__ == "__main__":
    find_honeypots()
