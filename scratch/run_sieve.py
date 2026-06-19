import json
import os
import sys
from datetime import datetime

# Add the scratch directory to python path to import sieve
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import sieve

def main():
    candidates_file = "C:/Users/Rushikesh/Desktop/Data/Hackathon/Hack2Skill-RedRob/Hackathon-Details/candidates.jsonl"
    
    scanned_count = 0
    honeypot_count = 0
    disqualified_count = 0
    union_filtered_count = 0
    passed_count = 0
    
    # Detailed stats
    stats = {
        "honeypot_yoe_mismatch": 0,
        "honeypot_job_duration_mismatch": 0,
        "honeypot_expert_zero_duration": 0,
        "dq_bad_title": 0,
        "dq_consulting_only": 0
    }
    
    # Grouped candidate IDs
    flagged_ids = {
        "honeypot": [],
        "bad_title": [],
        "consulting_only": [],
        "all_flagged": []
    }
    
    print("Starting sieve testing on candidates.jsonl...")
    start_time = datetime.now()
    
    with open(candidates_file, "r", encoding="utf-8") as f:
        for idx, line in enumerate(f):
            scanned_count += 1
            c = json.loads(line)
            cid = c["candidate_id"]
            
            is_hp, hp_triggers = sieve.is_honeypot(c)
            is_dq, dq_triggers = sieve.is_disqualified(c)
            
            # Record individual rule triggers
            if hp_triggers["yoe_mismatch"]:
                stats["honeypot_yoe_mismatch"] += 1
            if hp_triggers["job_duration_mismatch"]:
                stats["honeypot_job_duration_mismatch"] += 1
            if hp_triggers["expert_zero_duration"]:
                stats["honeypot_expert_zero_duration"] += 1
            if dq_triggers["bad_title"]:
                stats["dq_bad_title"] += 1
            if dq_triggers["consulting_only"]:
                stats["dq_consulting_only"] += 1
                
            flagged = False
            if is_hp:
                flagged_ids["honeypot"].append(cid)
                flagged = True
            if dq_triggers["bad_title"]:
                flagged_ids["bad_title"].append(cid)
                flagged = True
            if dq_triggers["consulting_only"]:
                flagged_ids["consulting_only"].append(cid)
                flagged = True
                
            if is_hp:
                honeypot_count += 1
            if is_dq:
                disqualified_count += 1
                
            if is_hp or is_dq:
                union_filtered_count += 1
                flagged_ids["all_flagged"].append(cid)
            else:
                passed_count += 1
                
            if scanned_count % 20000 == 0:
                print(f"  Processed {scanned_count} candidates...")
                
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    print("\n--- Sieve Results ---")
    print(f"Total candidates scanned: {scanned_count}")
    print(f"Honeypots identified: {honeypot_count}")
    print(f"Disqualified candidates: {disqualified_count}")
    print(f"Total unique candidates filtered (Honeypot OR Disqualified): {union_filtered_count}")
    print(f"Candidates passed: {passed_count}")
    print(f"Execution time: {duration:.2f} seconds")
    
    print("\nBreakdown of triggers:")
    for key, val in stats.items():
        print(f"  - {key}: {val} candidates")
        
    # Write flagged candidate IDs to a JSON file in the scratch folder
    out_file = "C:/Users/Rushikesh/Desktop/Data/Hackathon/Hack2Skill-RedRob/scratch/flagged_candidates.json"
    with open(out_file, "w", encoding="utf-8") as out_f:
        json.dump(flagged_ids, out_f, indent=2)
        
    print(f"\nFlagged candidate IDs written to: {out_file}")

if __name__ == "__main__":
    main()
