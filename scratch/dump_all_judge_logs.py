import json
from pathlib import Path

def dump_logs():
    subagents = {
        "industry_judge": "a565a918-d100-4a3c-abb4-26c5b84e618a",
        "ai_research_judge": "eba5d76e-839f-42d5-bdb6-d87fbd75c521",
        "product_judge": "59ec5176-4aa0-44dd-af2f-45f8335461c0",
        "engineering_judge": "9aace0ee-261c-44aa-a110-ef5249bb6d5f",
        "investor_judge": "1943d358-1b0a-4167-9865-ccbbfd081c48"
    }
    
    app_data_dir = Path("C:/Users/Rushikesh/.gemini/antigravity-cli/brain")
    
    for name, cid in subagents.items():
        log_path = app_data_dir / cid / ".system_generated" / "logs" / "transcript.jsonl"
        print(f"========================================\n{name} ({cid})\n========================================")
        if not log_path.exists():
            print(f"Log file does not exist: {log_path}\n")
            continue
            
        responses = []
        try:
            with open(log_path, "r", encoding="utf-8") as f:
                for line in f:
                    data = json.loads(line)
                    if data.get("type") == "PLANNER_RESPONSE":
                        content = data.get("content", "")
                        if content:
                            responses.append(content)
            
            # Print the last response which is typically the final report
            if responses:
                print(responses[-1])
            else:
                print("No planner response found.\n")
        except Exception as e:
            print(f"Error reading log: {e}\n")
        print("\n\n")

if __name__ == "__main__":
    dump_logs()
