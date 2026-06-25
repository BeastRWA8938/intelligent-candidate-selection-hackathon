import os
import json
import gzip
from datetime import datetime

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def inspect():
    # Load first 1000 candidates from candidates.jsonl to inspect distribution and find patterns
    candidates = []
    with open(os.path.join(PROJECT_ROOT, "Hackathon-Details", "candidates.jsonl"), "r", encoding="utf-8") as f:
        for i, line in enumerate(f):
            if i >= 1000:
                break
            candidates.append(json.loads(line))
    
    print(f"Loaded {len(candidates)} candidates for inspection.")
    
    # Let's inspect some field distributions
    countries = {}
    industries = {}
    experience_ranges = [0, 0, 0, 0, 0] # <3, 3-5, 5-9, 9-12, >12
    relocate_willing = 0
    work_modes = {}
    
    for c in candidates:
        prof = c["profile"]
        country = prof.get("country", "Unknown")
        countries[country] = countries.get(country, 0) + 1
        
        ind = prof.get("current_industry", "Unknown")
        industries[ind] = industries.get(ind, 0) + 1
        
        yoe = prof.get("years_of_experience", 0)
        if yoe < 3:
            experience_ranges[0] += 1
        elif yoe < 5:
            experience_ranges[1] += 1
        elif yoe <= 9:
            experience_ranges[2] += 1
        elif yoe <= 12:
            experience_ranges[3] += 1
        else:
            experience_ranges[4] += 1
            
        signals = c["redrob_signals"]
        if signals.get("willing_to_relocate", False):
            relocate_willing += 1
        wm = signals.get("preferred_work_mode", "Unknown")
        work_modes[wm] = work_modes.get(wm, 0) + 1

    print("\nCountry distribution in first 1000:")
    for k, v in sorted(countries.items(), key=lambda x: x[1], reverse=True)[:5]:
        print(f"  {k}: {v}")
        
    print("\nIndustry distribution in first 1000:")
    for k, v in sorted(industries.items(), key=lambda x: x[1], reverse=True)[:5]:
        print(f"  {k}: {v}")
        
    print(f"\nExperience distribution: <3y: {experience_ranges[0]}, 3-5y: {experience_ranges[1]}, 5-9y (Target): {experience_ranges[2]}, 9-12y: {experience_ranges[3]}, >12y: {experience_ranges[4]}")
    print(f"Willing to relocate: {relocate_willing} / 1000")
    print(f"Work modes: {work_modes}")

    # Let's search for potential honeypots or impossible profiles in the whole candidate pool (or first 10000)
    # We want to check for:
    # 1. Company tenure vs company founding (wait, where is company founding year? In description or is it a specific field? No, we don't have company founding database. Let's see how we can infer it or if there is another way).
    # 2. Expert proficiency with 0 months duration.
    # 3. Resume dates that overlap or are impossible.
    # 4. Expert in 10 skills with 0 years used.
    
    # Let's inspect some candidates in the pool to see if we can find any flagrant violations
    impossible_skill_duration = 0
    impossible_experience_dates = 0
    for i, c in enumerate(candidates):
        # Check skills: "expert" proficiency with 0 or very small duration_months
        expert_skills_with_low_duration = []
        for s in c.get("skills", []):
            if s.get("proficiency") == "expert" and s.get("duration_months", 0) <= 2:
                expert_skills_with_low_duration.append(s["name"])
        
        if len(expert_skills_with_low_duration) >= 5:
            impossible_skill_duration += 1
            if impossible_skill_duration <= 5:
                print(f"Candidate {c['candidate_id']} has impossible skills: {expert_skills_with_low_duration} with low duration!")
                
        # Check experience date overlap or future dates or negative duration
        for job in c.get("career_history", []):
            sd = job.get("start_date")
            ed = job.get("end_date")
            dur = job.get("duration_months", 0)
            if sd and ed:
                try:
                    s_dt = datetime.strptime(sd, "%Y-%m-%d")
                    e_dt = datetime.strptime(ed, "%Y-%m-%d")
                    calc_dur = (e_dt - s_dt).days / 30.4
                    if calc_dur < 0 or abs(calc_dur - dur) > 6: # deviation of more than 6 months
                        impossible_experience_dates += 1
                        if impossible_experience_dates <= 3:
                            print(f"Candidate {c['candidate_id']} has anomalous duration: {job['company']} {sd} to {ed} is {dur} months (calculated: {calc_dur:.1f})")
                except Exception as e:
                    pass

    print(f"\nHoneypot clues in first 1000:")
    print(f"  Expert skills with <= 2 months duration (>=5 skills): {impossible_skill_duration}")
    print(f"  Anomalous job durations: {impossible_experience_dates}")

if __name__ == "__main__":
    inspect()