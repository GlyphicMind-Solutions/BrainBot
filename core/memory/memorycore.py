# /BrainBot/core/memory/memorycore.py
# BrainBot Memory System
# Created by: David Kistner (Unconditional Love)


#system imports
import json
from datetime import datetime
from pathlib import Path

#pathing
CURRENT_DIR = Path(__file__).resolve().parent
CORE_ROOT = CURRENT_DIR.parent
AGENTS_ROOT = CORE_ROOT / "agents"


# =====================
# MEMORY CORE CLASS
# =====================
class MemoryCore:
    """
    Minimal agent memory controller.
    Stores a single agent.json file with:
    - name
    - identity
    - role
    - memory[]
    """
    # -----------
    # Initialize
    # -----------
    def __init__(self, base_path, agent_name, log=None):
        self.base = Path(base_path)
        self.agent_name = agent_name
        self.log = log or (lambda msg: print(msg))

        # Agent directory
        self.agent_dir = AGENTS_ROOT / agent_name
        self.agent_file = self.agent_dir / "agent.json"

        # Ensure directory exists
        self.agent_dir.mkdir(parents=True, exist_ok=True)

        # Load or seed agent.json
        if self.agent_file.exists():
            try:
                with open(self.agent_file, "r", encoding="utf-8") as f:
                    self.agent_data = json.load(f)
            except Exception as e:
                self.log(f"⚠️ Failed to load agent.json: {e}")
                self.agent_data = {}
        else:
            self.agent_data = {
                "name": agent_name,
                "identity": agent_name,
                "role": "agent",
                "memory": []
            }
            self._save()

        # Ensure required keys exist
        for key, default in [
            ("name", agent_name),
            ("identity", agent_name),
            ("role", "agent"),
            ("memory", [])
        ]:
            if key not in self.agent_data:
                self.agent_data[key] = default

        self._save()
    # -------------------------
    # Save agent.json
    # -------------------------
    def _save(self):
        try:
            with open(self.agent_file, "w", encoding="utf-8") as f:
                json.dump(self.agent_data, f, indent=2)
        except Exception as e:
            self.log(f"⚠️ Failed to save agent.json: {e}")
    # -------------------------
    # Add memory entry
    # -------------------------
    def store_memory(self, content, role="conversation"):
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "role": role,
            "content": content
        }
        self.agent_data["memory"].append(entry)
        self._save()
    # -------------------------
    # Load memory list
    # -------------------------
    def load_memory(self):
        return self.agent_data.get("memory", [])
    # -------------------------
    # Clear memory (optional)
    # -------------------------
    def clear_memory(self):
        self.agent_data["memory"] = []
        self._save()
    # ------------------
    # Log Event
    # ------------------
    def log_event(self, event_type, detail):
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "type": event_type,
            "detail": detail
        }
        self.agent_data["events"].append(entry)
        self._save()

