from __future__ import annotations

import json
import sys
from pathlib import Path

APP_DIR = Path(__file__).parent


def build_claude_desktop_config(server_name: str = "fomo") -> dict:
    """The exact snippet to paste into claude_desktop_config.json. Points at this app's
    own exe with a hidden --mcp-server flag when frozen (so Claude Desktop never needs a
    separate Python install to reach backend/mcp_server.py), or at the dev venv's
    interpreter + main.py otherwise."""
    if getattr(sys, "frozen", False):
        command = sys.executable
        args = ["--mcp-server"]
    else:
        command = sys.executable
        args = [str((APP_DIR / "main.py").resolve()), "--mcp-server"]

    return {
        "mcpServers": {
            server_name: {
                "command": command,
                "args": args,
            }
        }
    }


def build_claude_desktop_config_json(server_name: str = "fomo") -> str:
    return json.dumps(build_claude_desktop_config(server_name), indent=2)
