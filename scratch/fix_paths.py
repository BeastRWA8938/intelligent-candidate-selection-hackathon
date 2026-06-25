import os
import re

# Root path of the current workspace
WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def fix_file_paths(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    modified = False
    
    # Determine the relative depth to workspace root to define PROJECT_ROOT
    rel_path = os.path.relpath(file_path, WORKSPACE)
    parts = rel_path.split(os.sep)
    depth = len(parts) - 1
    
    if depth == 0:
        root_definition = "PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))"
    else:
        dirs_up = ", ".join(["os.path.dirname(os.path.abspath(__file__))"] + ["os.path.dirname"] * (depth - 1))
        if depth == 1:
            root_definition = "PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))"
        else:
            root_definition = f"PROJECT_ROOT = {dirs_up}" # fallback

    # 1. Replace candidates.jsonl absolute paths
    # Matches: "C:/Users/Rushikesh/Desktop/Data/Hackathon/Hack2Skill-RedRob/Hackathon-Details/candidates.jsonl"
    pattern_candidates = r'["\']C:/Users/Rushikesh/Desktop/Data/Hackathon/Hack2Skill-RedRob/Hackathon-Details/candidates\.jsonl["\']'
    if re.search(pattern_candidates, content, re.IGNORECASE):
        content = re.sub(
            pattern_candidates,
            'os.path.join(PROJECT_ROOT, "Hackathon-Details", "candidates.jsonl")',
            content,
            flags=re.IGNORECASE
        )
        modified = True

    # 2. Replace flagged_candidates.json absolute paths
    # Matches: "C:/Users/Rushikesh/Desktop/Data/Hackathon/Hack2Skill-RedRob/scratch/flagged_candidates.json"
    pattern_flagged = r'["\']C:/Users/Rushikesh/Desktop/Data/Hackathon/Hack2Skill-RedRob/scratch/flagged_candidates\.json["\']'
    if re.search(pattern_flagged, content, re.IGNORECASE):
        content = re.sub(
            pattern_flagged,
            'os.path.join(PROJECT_ROOT, "scratch", "flagged_candidates.json")',
            content,
            flags=re.IGNORECASE
        )
        modified = True

    # 3. Replace sample_candidates.json absolute paths
    pattern_sample = r'["\']C:/Users/Rushikesh/Desktop/Data/Hackathon/Hack2Skill-RedRob/Hackathon-Details/sample_candidates\.json["\']'
    if re.search(pattern_sample, content, re.IGNORECASE):
        content = re.sub(
            pattern_sample,
            'os.path.join(PROJECT_ROOT, "Hackathon-Details", "sample_candidates.json")',
            content,
            flags=re.IGNORECASE
        )
        modified = True

    # 4. Replace Hackathon-Details directory absolute path
    pattern_details_dir = r'Path\(["\']C:/Users/Rushikesh/Desktop/Data/Hackathon/Hack2Skill-RedRob/Hackathon-Details["\']\)'
    if re.search(pattern_details_dir, content, re.IGNORECASE):
        content = re.sub(
            pattern_details_dir,
            'Path(os.path.join(PROJECT_ROOT, "Hackathon-Details"))',
            content,
            flags=re.IGNORECASE
        )
        modified = True

    # 5. Replace app data / brain log paths
    pattern_brain = r'Path\(["\']C:/Users/Rushikesh/\.gemini/antigravity-(cli|ide)/brain["\']\)'
    if re.search(pattern_brain, content, re.IGNORECASE):
        content = re.sub(
            pattern_brain,
            'Path.home() / ".gemini" / "antigravity-cli" / "brain"',
            content,
            flags=re.IGNORECASE
        )
        modified = True

    pattern_artifacts = r'Path\(["\']C:/Users/Rushikesh/\.gemini/antigravity-(cli|ide)/brain/8e0c4dda-3621-4367-bc8a-b25854147947["\']\)'
    if re.search(pattern_artifacts, content, re.IGNORECASE):
        content = re.sub(
            pattern_artifacts,
            'Path.home() / ".gemini" / "antigravity-cli" / "brain" / "8e0c4dda-3621-4367-bc8a-b25854147947"',
            content,
            flags=re.IGNORECASE
        )
        modified = True

    # If we made dynamic changes using os/PROJECT_ROOT, ensure 'os' is imported and PROJECT_ROOT is defined
    if modified:
        # Check if 'import os' is present
        if "import os" not in content:
            # Insert after the first import or at start of file
            import_match = re.search(r"^(import \w+|from \w+ import)", content, re.MULTILINE)
            if import_match:
                content = content.replace(import_match.group(1), "import os\n" + import_match.group(1), 1)
            else:
                content = "import os\n" + content
        
        # Check if PROJECT_ROOT is already defined in the file
        if "PROJECT_ROOT =" not in content:
            # Insert PROJECT_ROOT definition right after imports
            # We look for a line starting with an import and define it after the import block
            lines = content.splitlines()
            last_import_idx = 0
            for idx, line in enumerate(lines):
                if line.startswith("import ") or line.startswith("from "):
                    last_import_idx = idx
            lines.insert(last_import_idx + 1, "")
            lines.insert(last_import_idx + 2, root_definition)
            content = "\n".join(lines)

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"[Fixed] {rel_path}")

def main():
    print("Starting automated path refactoring...")
    
    # We target python files in root, Hackathon-Details, and scratch directories
    dirs_to_scan = [
        WORKSPACE,
        os.path.join(WORKSPACE, "Hackathon-Details"),
        os.path.join(WORKSPACE, "scratch")
    ]
    
    for d in dirs_to_scan:
        for file in os.listdir(d):
            if file.endswith(".py") and file != "fix_paths.py":
                fix_file_paths(os.path.join(d, file))

if __name__ == "__main__":
    main()
