import json
from datetime import datetime

def find_high_quality():
    target_skills = {"embeddings", "retrieval", "ranking", "sentence-transformers", "pinecone", "weaviate", "qdrant", "milvus", "faiss", "elasticsearch", "hybrid search", "ndcg", "mrr", "map", "evaluation"}
    
    candidates = []
    
    with open("C:/Users/Rushikesh/Desktop/Data/Hackathon/Hack2Skill-RedRob/Hackathon-Details/candidates.jsonl", "r", encoding="utf-8") as f:
        for idx, line in enumerate(f):
            c = json.loads(line)
            
            # Skip honeypots (using a simplified check)
            yoe = c["profile"]["years_of_experience"]
            if yoe < 4 or yoe > 10:
                continue
                
            # Check skills
            skills = [s["name"].lower() for s in c.get("skills", [])]
            matching_skills = [s for s in skills if any(ts in s for ts in target_skills)]
            
            if len(matching_skills) >= 3:
                candidates.append(c)
                if len(candidates) <= 5:
                    print("="*60)
                    print(f"Candidate: {c['candidate_id']} | YoE: {yoe} | Location: {c['profile']['location']}, {c['profile']['country']}")
                    print(f"Title: {c['profile']['current_title']} | Company: {c['profile']['current_company']} ({c['profile']['current_company_size']})")
                    print(f"Skills matched: {matching_skills}")
                    print(f"Summary: {c['profile']['summary']}")
                    print("Career History Sample:")
                    for job in c["career_history"][:2]:
                        print(f"  {job['title']} at {job['company']} ({job['duration_months']}m): {job['description'][:150]}...")
                    print("="*60)
                    
            if idx > 0 and idx % 20000 == 0:
                pass
                
    print(f"\nTotal potential high-quality candidates found: {len(candidates)}")

if __name__ == "__main__":
    find_high_quality()
