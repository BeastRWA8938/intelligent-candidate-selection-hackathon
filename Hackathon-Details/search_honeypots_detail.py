import os
import json
import re

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def search():
    expert_zero_count = 0
    expert_zero_candidates = []
    word_founded_candidates = []
    digits_in_company = []
    
    with open(os.path.join(PROJECT_ROOT, "Hackathon-Details", "candidates.jsonl"), "r", encoding="utf-8") as f:
        for idx, line in enumerate(f):
            c = json.loads(line)
            cid = c["candidate_id"]
            
            # Check 1: Expert skills with 0 duration_months
            expert_zero_skills = [s["name"] for s in c.get("skills", []) if s.get("proficiency") == "expert" and s.get("duration_months", 0) == 0]
            if len(expert_zero_skills) > 0:
                expert_zero_count += 1
                expert_zero_candidates.append((cid, len(expert_zero_skills), expert_zero_skills))
                
            # Check 2: The word "founded" in the entire JSON string
            json_str = line.lower()
            if "founded" in json_str:
                word_founded_candidates.append(cid)
                
            # Check 3: Company names with numbers (like 2020, 2021, 2022, 2023, 2024, 2025)
            for job in c.get("career_history", []):
                comp = job.get("company", "")
                m = re.search(r"\b(201\d|202\d)\b", comp)
                if m:
                    digits_in_company.append((cid, comp, job.get("start_date"), job.get("duration_months")))
                    
    print(f"Total candidates with any expert skill having 0 duration: {expert_zero_count}")
    print(f"Total candidates containing the word 'founded': {len(word_founded_candidates)}")
    print(f"Total candidates with digits in company name: {len(digits_in_company)}")
    
    if expert_zero_candidates:
        print("\nSample expert-zero candidates (sorted by count of expert-zero skills):")
        expert_zero_candidates.sort(key=lambda x: x[1], reverse=True)
        for ec in expert_zero_candidates[:10]:
            print(f"  {ec[0]}: {ec[1]} skills: {ec[2]}")
            
    if word_founded_candidates:
        print("\nSample 'founded' candidates:", word_founded_candidates[:10])
        
    if digits_in_company:
        print("\nSample company digits candidates:")
        for dc in digits_in_company[:10]:
            print(f"  {dc[0]}: Company='{dc[1]}', Start={dc[2]}, Duration={dc[3]} months")

if __name__ == "__main__":
    search()