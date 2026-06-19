import json
from datetime import datetime
import re
import collections

# Inline copy of the is_honeypot logic and helper functions from rank.py to check which rule triggers
def parse_date(date_str, current_time):
    if not date_str:
        return None
    date_str = str(date_str).strip()
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%Y-%m", "%Y"):
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    year_match = re.search(r"\b(19\d\d|20\d\d)\b", date_str)
    if year_match:
        try:
            return datetime(int(year_match.group(1)), 1, 1)
        except:
            pass
    return None

def is_honeypot_detailed(c, current_time):
    yoe = c.get("profile", {}).get("years_of_experience")
    if yoe is None or not isinstance(yoe, (int, float)):
        yoe = 0.0
    yoe = float(yoe)
    
    history = c.get("career_history", [])
    first_start = None
    for job in history:
        sd = job.get("start_date")
        if sd:
            s_dt = parse_date(sd, current_time)
            if s_dt:
                if first_start is None or s_dt < first_start:
                    first_start = s_dt
                    
    yoe_triggered = False
    if first_start:
        span_years = (current_time - first_start).days / 365.25
        if yoe > span_years + 2.0:
            yoe_triggered = True
            
    dur_triggered = False
    dur_details = []
    for job in history:
        sd = job.get("start_date")
        ed = job.get("end_date")
        dur = job.get("duration_months")
        if dur is None or not isinstance(dur, (int, float)):
            dur = 0.0
        dur = float(dur)
        
        if sd:
            s_dt = parse_date(sd, current_time)
            if s_dt:
                if ed:
                    e_dt = parse_date(ed, current_time)
                else:
                    e_dt = current_time
                if e_dt:
                    calc_dur = (e_dt - s_dt).days / 30.4
                    if dur > calc_dur + 3.0:
                        dur_triggered = True
                        dur_details.append(f"company: {job.get('company')}, dur: {dur}, calc_dur: {calc_dur:.2f}, sd: {sd}, ed: {ed}")
                        break
                        
    expert_zero_skills = []
    for s in c.get("skills", []):
        prof_level = s.get("proficiency")
        if isinstance(prof_level, str) and prof_level.lower().strip() == "expert":
            dur = s.get("duration_months", 0)
            if dur is None or dur == 0:
                expert_zero_skills.append(s.get("name", ""))
                
    skills_triggered = len(expert_zero_skills) >= 4
    
    sal_triggered = False
    sal = c.get("redrob_signals", {}).get("expected_salary_range_inr_lpa", {})
    if sal:
        s_min = sal.get("min")
        s_max = sal.get("max")
        if s_min is not None and s_max is not None:
            if isinstance(s_min, (int, float)) and isinstance(s_max, (int, float)):
                if s_min > s_max:
                    sal_triggered = True
                    
    return yoe_triggered, dur_triggered, dur_details, skills_triggered, sal_triggered

def diagnose():
    candidates_file = "./Hackathon-Details/candidates.jsonl"
    current_time = datetime(2026, 6, 18)
    
    counts = collections.defaultdict(int)
    examples = collections.defaultdict(list)
    
    with open(candidates_file, "r", encoding="utf-8") as f:
        for idx, line in enumerate(f):
            if idx >= 2000: # Check first 2000 profiles
                break
            c = json.loads(line)
            cid = c["candidate_id"]
            
            yoe_t, dur_t, dur_det, skill_t, sal_t = is_honeypot_detailed(c, current_time)
            
            if yoe_t:
                counts["yoe"] += 1
                if len(examples["yoe"]) < 3:
                    examples["yoe"].append((cid, c["profile"]["years_of_experience"], c["career_history"]))
            if dur_t:
                counts["duration"] += 1
                if len(examples["duration"]) < 3:
                    examples["duration"].append((cid, dur_det, c["career_history"]))
            if skill_t:
                counts["skills"] += 1
                if len(examples["skills"]) < 3:
                    examples["skills"].append((cid, c.get("skills", [])))
            if sal_t:
                counts["salary"] += 1
                if len(examples["salary"]) < 3:
                    examples["salary"].append((cid, c["redrob_signals"]["expected_salary_range_inr_lpa"]))
                    
    print("=== Diagnostic Results ===")
    for k, v in counts.items():
        print(f"Rule '{k}' triggered {v} times out of 2000 profiles.")
        
    for k, evs in examples.items():
        print(f"\n--- Examples of '{k}' ---")
        for ev in evs:
            print(f"Candidate: {ev[0]}")
            if k == "yoe":
                print(f"  YoE: {ev[1]}")
                print(f"  Jobs: {[{'company': j.get('company'), 'sd': j.get('start_date'), 'ed': j.get('end_date')} for j in ev[2]]}")
            elif k == "duration":
                print(f"  Duration Details: {ev[1]}")
                print(f"  Jobs: {[{'company': j.get('company'), 'sd': j.get('start_date'), 'ed': j.get('end_date'), 'dur': j.get('duration_months')} for j in ev[2]]}")
            elif k == "skills":
                print(f"  Skills: {[{'name': s.get('name'), 'proficiency': s.get('proficiency'), 'dur': s.get('duration_months')} for s in ev[1][:5]]}")
            elif k == "salary":
                print(f"  Salary: {ev[1]}")

if __name__ == "__main__":
    diagnose()
