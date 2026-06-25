import os
import json
import re
from datetime import datetime

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def scan_candidates():
    # We will search for:
    # 1. Expert skills with 0 (or very low) duration_months.
    # 2. Impossible experience: years of experience at a company compared to its founding year in description.
    # 3. Any other weird signals: e.g. expert in 10 skills with 0 years.
    # 4. Total experience vs career history duration.
    # Let's count and inspect.
    
    count = 0
    honeypots = []
    
    with open(os.path.join(PROJECT_ROOT, "Hackathon-Details", "candidates.jsonl"), "r", encoding="utf-8") as f:
        for idx, line in enumerate(f):
            c = json.loads(line)
            cid = c["candidate_id"]
            
            # Check 1: 'expert' proficiency in 10 skills with 0 years/months used
            expert_zero_dur = 0
            for s in c.get("skills", []):
                if s.get("proficiency") == "expert" and s.get("duration_months", 0) <= 0:
                    expert_zero_dur += 1
            
            # Check 2: company founding vs tenure
            # Look for phrases like "founded in XXXX" or "founded Y years ago" in career description
            founding_anomaly = False
            for job in c.get("career_history", []):
                desc = job.get("description", "")
                company = job.get("company", "")
                start_date_str = job.get("start_date")
                duration = job.get("duration_months", 0)
                
                # Check if description mentions founding year
                # E.g., "founded in 2023" or "founded 3 years ago"
                # Let's look for "founded in (digit{4})"
                match = re.search(r"founded in (\d{4})", desc, re.IGNORECASE)
                if match:
                    founding_year = int(match.group(1))
                    if start_date_str:
                        start_year = int(start_date_str.split("-")[0])
                        # If start year is before founding year, it's impossible!
                        if start_year < founding_year:
                            founding_anomaly = True
                            job_anomaly_desc = f"Started in {start_year} at {company} founded in {founding_year}"
                
                # Check for "founded Y years ago"
                # If the current date is 2026-06-18, and it was "founded 3 years ago" (i.e. 2023),
                # but they worked there for 8 years (96 months) or started in 2018.
                match_ago = re.search(r"founded (\d+)\s+years?\s+ago", desc, re.IGNORECASE)
                if match_ago:
                    years_ago = int(match_ago.group(1))
                    founding_year = 2026 - years_ago
                    if start_date_str:
                        start_year = int(start_date_str.split("-")[0])
                        if start_year < founding_year:
                            founding_anomaly = True
                            job_anomaly_desc = f"Started in {start_year} at {company} founded {years_ago} years ago (founded {founding_year})"
            
            # Let's see if we have candidates matching these
            is_honeypot = False
            reasons = []
            if expert_zero_dur >= 10:
                is_honeypot = True
                reasons.append(f"Expert in {expert_zero_dur} skills with 0 months duration")
            if founding_anomaly:
                is_honeypot = True
                reasons.append(job_anomaly_desc)
                
            if is_honeypot:
                honeypots.append((cid, reasons))
                if len(honeypots) <= 10:
                    print(f"Honeypot found: {cid} - {reasons}")
                    
    print(f"\nTotal potential honeypots found: {len(honeypots)}")

if __name__ == "__main__":
    scan_candidates()