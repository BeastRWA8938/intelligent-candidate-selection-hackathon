import json
from datetime import datetime

def search():
    negative_durations = 0
    future_jobs = 0
    with open("C:/Users/Rushikesh/Desktop/Data/Hackathon/Hack2Skill-RedRob/Hackathon-Details/candidates.jsonl", "r", encoding="utf-8") as f:
        for idx, line in enumerate(f):
            c = json.loads(line)
            cid = c["candidate_id"]
            
            for job in c.get("career_history", []):
                sd = job.get("start_date")
                ed = job.get("end_date")
                if sd and ed:
                    try:
                        s_dt = datetime.strptime(sd, "%Y-%m-%d")
                        e_dt = datetime.strptime(ed, "%Y-%m-%d")
                        if s_dt > e_dt:
                            negative_durations += 1
                            print(f"[{cid}] Negative job: {sd} to {ed}")
                    except:
                        pass
                if sd:
                    try:
                        s_dt = datetime.strptime(sd, "%Y-%m-%d")
                        if s_dt > datetime(2026, 6, 18):
                            future_jobs += 1
                            print(f"[{cid}] Future job: {sd}")
                    except:
                        pass
    print(f"Negative durations: {negative_durations}")
    print(f"Future jobs: {future_jobs}")

if __name__ == "__main__":
    search()
