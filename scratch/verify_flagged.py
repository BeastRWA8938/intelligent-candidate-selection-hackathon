import json

def verify():
    file_path = "C:/Users/Rushikesh/Desktop/Data/Hackathon/Hack2Skill-RedRob/scratch/flagged_candidates.json"
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    honeypots = data["honeypot"]
    bad_titles = data["bad_title"]
    consulting_only = data["consulting_only"]
    all_flagged = data["all_flagged"]
    
    print(f"Honeypots: {len(honeypots)}")
    print(f"Bad Titles: {len(bad_titles)}")
    print(f"Consulting Only: {len(consulting_only)}")
    print(f"Total Unique Flagged: {len(all_flagged)}")
    
    # Overlap between honeypot and disqualified
    dq_set = set(bad_titles).union(set(consulting_only))
    overlap = set(honeypots).intersection(dq_set)
    print(f"Overlap between Honeypots and Disqualified (Bad Title / Consulting): {len(overlap)}")
    
    print("\nExact Honeypot Candidate IDs:")
    print(sorted(honeypots))

if __name__ == "__main__":
    verify()
