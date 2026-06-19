import json
from datetime import datetime

def scan_full():
    anomalous_yoe = []
    anomalous_job_dur = []
    impossible_skill_dur = []
    date_format_errors = 0
    total = 0
    
    current_time = datetime(2026, 6, 18)
    
    with open("C:/Users/Rushikesh/Desktop/Data/Hackathon/Hack2Skill-RedRob/Hackathon-Details/candidates.jsonl", "r", encoding="utf-8") as f:
        for idx, line in enumerate(f):
            total += 1
            c = json.loads(line)
            cid = c["candidate_id"]
            yoe = c["profile"]["years_of_experience"]
            history = c["career_history"]
            
            # Check 1: YoE vs first job start date
            first_start = None
            for job in history:
                sd = job.get("start_date")
                if sd:
                    try:
                        s_dt = datetime.strptime(sd, "%Y-%m-%d")
                        if first_start is None or s_dt < first_start:
                            first_start = s_dt
                    except:
                        date_format_errors += 1
            
            if first_start:
                span_years = (current_time - first_start).days / 365.25
                if yoe > span_years + 0.5:
                    anomalous_yoe.append((cid, yoe, first_start.strftime("%Y-%m-%d"), span_years))
            
            # Check 2: job date-duration discrepancy
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
                        if dur > calc_dur + 12: # duration is larger than calendar dates by more than a year
                            anomalous_job_dur.append((cid, job["company"], sd, ed, dur, calc_dur))
                    except:
                        pass
                        
            # Check 3: 'expert' proficiency skills with 0 duration
            expert_zero_skills = [s["name"] for s in c.get("skills", []) if s.get("proficiency") == "expert" and s.get("duration_months", 0) == 0]
            if len(expert_zero_skills) >= 5:
                impossible_skill_dur.append((cid, len(expert_zero_skills), expert_zero_skills))

            if idx > 0 and idx % 20000 == 0:
                print(f"Processed {idx}...")

    print(f"\nScan results for {total} candidates:")
    print(f"Candidates with anomalous YoE (YoE > max span of jobs): {len(anomalous_yoe)}")
    print(f"Candidates with anomalous job duration (stated duration > calendar span): {len(anomalous_job_dur)}")
    print(f"Candidates with >=5 expert skills having 0 duration: {len(impossible_skill_dur)}")
    print(f"Date format errors: {date_format_errors}")
    
    if anomalous_yoe:
        print("\nSample anomalous YoE:")
        for ay in anomalous_yoe[:5]:
            print(f"  {ay[0]}: YoE={ay[1]}, first job={ay[2]}, max span={ay[3]:.2f} years")
            
    if anomalous_job_dur:
        print("\nSample anomalous job duration:")
        for ajd in anomalous_job_dur[:5]:
            print(f"  {ajd[0]}: Company={ajd[1]}, dates={ajd[2]} to {ajd[3]}, stated={ajd[4]} months, calc={ajd[5]:.1f} months")

if __name__ == "__main__":
    scan_full()
