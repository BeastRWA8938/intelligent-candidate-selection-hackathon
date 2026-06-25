import os
import json
from pathlib import Path

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

def read_logs():
    subagents = {
        "industry_judge": "a565a918-d100-4a3c-abb4-26c5b84e618a",
        "ai_research_judge": "eba5d76e-839f-42d5-bdb6-d87fbd75c521",
        "product_judge": "59ec5176-4aa0-44dd-af2f-45f8335461c0",
        "engineering_judge": "9aace0ee-261c-44aa-a110-ef5249bb6d5f",
        "investor_judge": "1943d358-1b0a-4167-9865-ccbbfd081c48"
    }
    
    app_data_dir = Path.home() / ".gemini" / "antigravity-cli" / "brain"
    
    for name, cid in subagents.items():
        log_path = app_data_dir / cid / ".system_generated" / "logs" / "transcript.jsonl"
        print(f"Reading log for {name} ({cid})...")
        if not log_path.exists():
            print(f"  Log file does not exist: {log_path}")
            continue
            
        last_msg = None
        try:
            with open(log_path, "r", encoding="utf-8") as f:
                for line in f:
                    data = json.loads(line)
                    if data.get("type") == "PLANNER_RESPONSE":
                        last_msg = data.get("content", "")
            if last_msg:
                print(f"--- {name} Output ---")
                print(last_msg[:1200]) # Print first 1200 chars
                print("-----------------------\n")
            else:
                print("  No planner response found.\n")
        except Exception as e:
            print(f"  Error reading log: {e}\n")

if __name__ == "__main__":
    read_logs()