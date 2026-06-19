import json

CONSULTING_COMPANIES = {
    "tcs", "tata consultancy services", "infosys", "wipro", "accenture", 
    "cognizant", "capgemini", "hcl", "tech mahindra", "l&t", "lnt", 
    "mindtree", "mphasis", "ust global", "hexaware"
}

def check_consulting():
    consulting_only_count = 0
    total = 0
    
    with open("C:/Users/Rushikesh/Desktop/Data/Hackathon/Hack2Skill-RedRob/Hackathon-Details/candidates.jsonl", "r", encoding="utf-8") as f:
        for idx, line in enumerate(f):
            total += 1
            c = json.loads(line)
            
            history = c.get("career_history", [])
            all_consulting = True
            for job in history:
                comp = job.get("company", "").lower().strip()
                is_consult = any(cs in comp for cs in CONSULTING_COMPANIES)
                if not is_consult:
                    all_consulting = False
                    break
            
            if all_consulting and history:
                consulting_only_count += 1
                
    print(f"Total candidates: {total}")
    print(f"Candidates who worked ONLY at consulting firms: {consulting_only_count} ({consulting_only_count / total * 100:.2f}%)")

if __name__ == "__main__":
    check_consulting()
