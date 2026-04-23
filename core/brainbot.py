# /BrainBot/core/brainbot.py
# BrainBot Main Controller
# Created by: David Kistner (Unconditional Love)


# system imports
import json
from pathlib import Path

# folder imports
from core.memory.memorycore import MemoryCore
from core.senses.senses import SensesController
from core.llm.llm_controller import LLMController


# Repo-local base paths
CURRENT_DIR = Path(__file__).resolve().parent          # /BrainBot/core
BRAINBOT_ROOT = CURRENT_DIR.parent                     # /BrainBot
BASE_PATH = BRAINBOT_ROOT

# Agents root (system + agents share this root)
AGENTS_ROOT = BASE_PATH / "core" / "agents"


# ========================
# BRAINBOT CLASS
# ========================
class BrainBot:
    # -----------------
    # Initialize
    # -----------------
    def __init__(self, base_path=BASE_PATH, log=None, chat=None):
        # Base setup
        self.base = Path(base_path)
        self.log = log or (lambda msg: print(msg))
        self.chat = chat or (lambda msg: None)

        # Audio flags
        self.audio_input_enabled = False
        self.audio_output_enabled = False

        # Shared LLM controller (manifest-driven)
        self.llm = LLMController(base_path=self.base, log=self.log)

        # BrainBot does not have its own memory file.
        self.memory = None

        # Senses (for optional audio I/O)
        self.senses = SensesController(
            log=self.log
        )

        # Active agent context (used by GUI / DialogueManager)
        self.active_agent = None

        self.log("✅ BrainBot core initialized (standalone mode).")

# ==============================
# Response Functionality
# ==============================
    # ------------------------------------------------------------
    # Main respond
    # ------------------------------------------------------------
    def respond(self, text, agent=None, source="text"):
        """
        Main BrainBot response function.

        :param text:   user input text
        :param agent:  optional agent context dict (with 'llm', 'memory', etc.)
        :param source: 'text' or 'voice' (for future routing)
        """

        raw_text = (text or "").strip()
        if not raw_text:
            return ""

        # Ignore voice input if disabled
        if source == "voice" and not self.audio_input_enabled:
            return "(Audio input disabled)"

        # Determine LLM backend
        llm_key = None
        if agent and isinstance(agent, dict) and "llm" in agent:
            llm_key = agent["llm"]
        else:
            # Try default model on controller
            if hasattr(self.llm, "default_model") and self.llm.default_model:
                llm_key = self.llm.default_model
            elif getattr(self.llm, "models", None):
                # Fallback: first model in manifest
                try:
                    llm_key = next(iter(self.llm.models.keys()))
                except Exception:
                    llm_key = None

        if not llm_key:
            self.log("⚠️ No LLM backend available for respond().")
            return "⚠️ No LLM backend is configured. Please add a model in manifest.yaml."

        # Query the LLM
        try:
            reply = self.llm.query(
                raw_text,
                llm=llm_key,
                persona=agent
            )
        except Exception as e:
            self.log(f"⚠️ LLM query failed: {e}")
            reply = "⚠️ Internal LLM error."

        # Store memory (simple dialogue pair)
        try:
            self.memory.store_shortterm(
                role="conversation",
                content=f"Q: {raw_text}\nA: {reply}",
                glyph="💬",
                thoughts="Dialogue pair",
                source_type="dialogue"
            )
        except Exception as e:
            self.log(f"⚠️ Memory store failed: {e}")

        # Optional audio output
        if self.audio_output_enabled:
            try:
                self.senses.audio.synthesize_speech(reply, agent=agent)
            except Exception as e:
                self.log(f"⚠️ Audio output failed: {e}")

        return reply
# ================================
# Voice Functionality
# ================================
    # ------------------
    # Voice tuning
    # ------------------
    def tune_agent_voice(self, agent_name, filepath):
        """
        Load a voice profile from an audio file and attach it to an agent.
        """

        profile = self.senses.audio.load_voice_profile(filepath)
        if not profile:
            return "⚠️ Failed to load voice profile."

        agent_mem = MemoryCore(str(AGENTS_ROOT), agent_name, log=self.log)
        agent_mem.agent_data["voice_profile"] = profile
        agent_mem._save_agent()
        return f"🎙️ Voice tuned for agent {agent_name}."
    # -----------------------
    # Audio toggle - Input
    # -----------------------
    def toggle_audio_input(self, enabled: bool):
        self.audio_input_enabled = bool(enabled)
        state = "enabled" if self.audio_input_enabled else "disabled"
        msg = f"🎙️ Audio input {state}."
        self.log(msg)
        return msg
    # -----------------------
    # Audio toggle - Output
    # -----------------------
    def toggle_audio_output(self, enabled: bool):
        self.audio_output_enabled = bool(enabled)
        state = "enabled" if self.audio_output_enabled else "disabled"
        msg = f"🔊 Audio output {state}."
        self.log(msg)
        return msg

