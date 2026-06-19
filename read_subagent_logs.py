import json
from pathlib import Path

def read_logs():
    subagents = {
        "resume_parsing_expert": "690f4bd5-2c35-4354-9b4c-fe1f187cb210",
        "agent_systems_engineer": "405ce881-0ba4-43dc-a665-de9611a84266",
        "evaluation_engineer": "09932690-3910-43c5-a5a2-7b743858aa7d"
    }
    
    app_data_dir = Path("C:/Users/Rushikesh/.gemini/antigravity-cli/brain")
    
    for name, cid in subagents.items():
        log_path = app_data_dir / cid / ".system_generated" / "logs" / "transcript.jsonl"
        print(f"Reading log for {name} ({cid})...")
        if not log_path.exists():
            print(f"  Log file does not exist: {log_path}")
            continue
            
        # Read the lines and find the last planner response or agent message
        last_msg = None
        try:
            with open(log_path, "r", encoding="utf-8") as f:
                for line in f:
                    data = json.loads(line)
                    # We look for steps where the agent outputs its final text
                    if data.get("type") == "PLANNER_RESPONSE":
                        last_msg = data.get("content", "")
            if last_msg:
                print(f"--- {name} Output ---")
                print(last_msg[:1000]) # Print first 1000 chars
                print("-----------------------\n")
            else:
                print("  No planner response found.\n")
        except Exception as e:
            print(f"  Error reading log: {e}\n")

if __name__ == "__main__":
    read_logs()
