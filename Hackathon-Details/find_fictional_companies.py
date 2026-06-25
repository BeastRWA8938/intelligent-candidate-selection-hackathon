import os
import json

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def find_fictional():
    # We want to check what companies are present in the career history of candidates, 
    # and if there are obvious fictional ones from movies/TV shows/games.
    fictional_names = {
        "stark industries", "wayne enterprises", "hooli", "initech", "globex", 
        "dunder mifflin", "tyrell corp", "aperture science", "umbrella corp", 
        "acme corp", "oscorp", "lexcorp", "vandelay industries", "bluth company",
        "cyberdyne systems", "massive dynamic", "veidt enterprises", "hudsucker",
        "virtucon", "gringotts", "wonka industries", "soylent corporation",
        "shinjuku corporation", "pennypacker", "kramerica"
    }
    
    match_count = 0
    matched_companies = {}
    
    with open(os.path.join(PROJECT_ROOT, "Hackathon-Details", "candidates.jsonl"), "r", encoding="utf-8") as f:
        for idx, line in enumerate(f):
            c = json.loads(line)
            cid = c["candidate_id"]
            
            for job in c.get("career_history", []):
                comp = job.get("company", "").lower().strip()
                for fn in fictional_names:
                    if fn in comp:
                        matched_companies[comp] = matched_companies.get(comp, 0) + 1
                        match_count += 1
                        
            if idx > 0 and idx % 20000 == 0:
                pass
                
    print(f"Total fictional company matches: {match_count}")
    print("Fictional companies found and their counts:")
    for k, v in sorted(matched_companies.items(), key=lambda x: x[1], reverse=True):
        print(f"  {k}: {v}")

if __name__ == "__main__":
    find_fictional()