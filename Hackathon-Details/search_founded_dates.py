import os
import json
import re

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def search_years():
    matches = []
    # Match any 4 digit number that could be a year in descriptions
    year_pat = re.compile(r"\b(19\d{2}|20\d{2})\b")
    
    with open(os.path.join(PROJECT_ROOT, "Hackathon-Details", "candidates.jsonl"), "r", encoding="utf-8") as f:
        for idx, line in enumerate(f):
            c = json.loads(line)
            cid = c["candidate_id"]
            
            for job in c.get("career_history", []):
                desc = job.get("description", "")
                ms = year_pat.findall(desc)
                if ms:
                    matches.append((cid, job["company"], ms, desc))
                    if len(matches) <= 20:
                        print(f"[{cid}] Company={job['company']} Years={ms} \n  Desc={desc[:150]}...")
            if idx > 0 and idx % 20000 == 0:
                print(f"Processed {idx}...")
                
    print(f"Total matching descriptions with years: {len(matches)}")

if __name__ == "__main__":
    search_years()