import json

def inspect_candidates():
    target_ids = ["CAND_0003430", "CAND_0007353", "CAND_0016000", "CAND_0008960"]
    
    with open("C:/Users/Rushikesh/Desktop/Data/Hackathon/Hack2Skill-RedRob/Hackathon-Details/candidates.jsonl", "r", encoding="utf-8") as f:
        for line in f:
            c = json.loads(line)
            if c["candidate_id"] in target_ids:
                print("="*60)
                print(f"Candidate: {c['candidate_id']}")
                print(f"YoE: {c['profile']['years_of_experience']}")
                print("Skills:")
                for s in c["skills"][:10]:
                    print(f"  {s['name']}: {s['proficiency']} ({s.get('duration_months')}m)")
                print("Career History:")
                for job in c["career_history"]:
                    print(f"  Company: {job['company']}")
                    print(f"  Title: {job['title']}")
                    print(f"  Dates: {job['start_date']} to {job['end_date']}")
                    print(f"  Duration: {job['duration_months']}m")
                    print(f"  Description: {job['description']}")
                print("Redrob Signals:")
                print(json.dumps(c["redrob_signals"], indent=2))
                print("="*60)

if __name__ == "__main__":
    inspect_candidates()
