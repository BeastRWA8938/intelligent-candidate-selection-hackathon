import json
from pathlib import Path

def extract_and_save_reports():
    subagents = {
        "industry_judge": "a565a918-d100-4a3c-abb4-26c5b84e618a",
        "ai_research_judge": "eba5d76e-839f-42d5-bdb6-d87fbd75c521",
        "product_judge": "59ec5176-4aa0-44dd-af2f-45f8335461c0",
        "engineering_judge": "9aace0ee-261c-44aa-a110-ef5249bb6d5f",
        "investor_judge": "1943d358-1b0a-4167-9865-ccbbfd081c48"
    }
    
    app_data_dir = Path("C:/Users/Rushikesh/.gemini/antigravity-cli/brain")
    artifacts_dir = Path("C:/Users/Rushikesh/.gemini/antigravity-cli/brain/8e0c4dda-3621-4367-bc8a-b25854147947")
    
    for name, cid in subagents.items():
        log_path = app_data_dir / cid / ".system_generated" / "logs" / "transcript_full.jsonl"
        if not log_path.exists():
            log_path = app_data_dir / cid / ".system_generated" / "logs" / "transcript.jsonl"
            
        if not log_path.exists():
            print(f"Log file does not exist for {name}: {log_path}")
            continue
            
        report_content = None
        # Try finding send_message call
        try:
            with open(log_path, "r", encoding="utf-8") as f:
                for line in f:
                    data = json.loads(line)
                    tool_calls = data.get("tool_calls", [])
                    for tc in tool_calls:
                        method = tc.get("method") or tc.get("name") or ""
                        if "send_message" in method:
                            args = tc.get("args") or tc.get("arguments") or {}
                            msg_content = args.get("Message") or args.get("message")
                            if msg_content:
                                report_content = msg_content
                                break
        except Exception as e:
            print(f"Error parsing log for {name}: {e}")
            
        if not report_content:
            # Try finding last PLANNER_RESPONSE containing markdown headers or score
            try:
                with open(log_path, "r", encoding="utf-8") as f:
                    last_pr = None
                    for line in f:
                        data = json.loads(line)
                        if data.get("type") == "PLANNER_RESPONSE":
                            content = data.get("content", "")
                            if "#" in content or "score" in content.lower():
                                last_pr = content
                    if last_pr:
                        report_content = last_pr
            except Exception as e:
                pass
                
        if report_content:
            output_file = artifacts_dir / f"{name}_report.md"
            with open(output_file, "w", encoding="utf-8") as f_out:
                f_out.write(report_content)
            print(f"Saved report for {name} to {output_file.name}")
        else:
            print(f"No report found for {name}")

if __name__ == "__main__":
    extract_and_save_reports()
