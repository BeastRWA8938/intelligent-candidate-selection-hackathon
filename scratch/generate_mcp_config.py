import os
import json

workspace = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
python_exe = os.path.join(workspace, "venv", "Scripts", "python.exe")
if not os.path.exists(python_exe):
    # Fallback to standard python path on linux/mac
    python_exe = os.path.join(workspace, "venv", "bin", "python")

config = {
  "mcpServers": {
    "ppt": {
      "command": python_exe,
      "args": [
        os.path.join(workspace, "PPT", "Office-PowerPoint-MCP-Server", "ppt_mcp_server.py")
      ],
      "env": {
        "PYTHONPATH": os.path.join(workspace, "PPT", "Office-PowerPoint-MCP-Server"),
        "PPT_TEMPLATE_PATH": os.path.join(workspace, "PPT", "Office-PowerPoint-MCP-Server", "templates")
      }
    }
  }
}

config_path = os.path.join(workspace, "mcp-config.json")
with open(config_path, "w", encoding="utf-8") as f:
    json.dump(config, f, indent=2)

print(f"[Generated] MCP configuration written to: {config_path}")
