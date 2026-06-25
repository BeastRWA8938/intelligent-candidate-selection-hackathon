import os
import json
import re

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def inspect_details():
    # Let's read first 5000 candidates and search for the word "founded" (case insensitive)
    # and print some examples.
    print("Searching for 'founded' in first 5000 candidates...")
    found_count = 0
    with open(os.path.join(PROJECT_ROOT, "Hackathon-Details", "candidates.jsonl"), "r", encoding="utf-8") as f:
        for idx, line in enumerate(f):
            if idx >= 5000:
                break
            c = json.loads(line)
            cid = c["candidate_id"]
            
            # check summary and job descriptions
            summary = c["profile"].get("summary", "")
            if "founded" in summary.lower():
                print(f"[{cid}] Summary: ... {summary[:150]} ...")
                found_count += 1
                
            for job in c.get("career_history", []):
                desc = job.get("description", "")
                if "founded" in desc.lower():
                    print(f"[{cid}] Job desc: ... {desc[:150]} ...")
                    found_count += 1
                    
            if found_count >= 10:
                break
                
    # Also let's inspect the skills list of the first candidate
    with open(os.path.join(PROJECT_ROOT, "Hackathon-Details", "candidates.jsonl"), "r", encoding="utf-8") as f:
        c = json.loads(f.readline())
        print("\nFirst candidate skills sample:")
        print(json.dumps(c["skills"][:5], indent=2))
        
        print("\nFirst candidate redrob_signals sample:")
        print(json.dumps(c["redrob_signals"], indent=2))

if __name__ == "__main__":
    inspect_details()