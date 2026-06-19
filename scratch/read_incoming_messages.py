import json
from pathlib import Path

def read_messages():
    transcript_path = Path("C:/Users/Rushikesh/.gemini/antigravity-cli/brain/8e0c4dda-3621-4367-bc8a-b25854147947/.system_generated/logs/transcript.jsonl")
    if not transcript_path.exists():
        print("Transcript does not exist.")
        return
        
    with open(transcript_path, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            try:
                data = json.loads(line)
                # Look for messages received from subagents (often with priority or content containing reports)
                content = data.get("content", "")
                if not content:
                    continue
                
                # Check if it mentions "Industry Judge", "AI Research", "Product Judge", "Engineering Judge", or "Investor Judge"
                # and contains significant reports or evaluation feedback
                lower_content = content.lower()
                if "judge" in lower_content or "score" in lower_content:
                    print(f"--- Message in Step {data.get('step_index', line_num)} (Type: {data.get('type')}) ---")
                    print(content[:3000]) # Print first 3000 chars of matching steps
                    print("="*60 + "\n")
            except Exception as e:
                pass

if __name__ == "__main__":
    read_messages()
