# /BrainBot/core/llm/llm_controller.py
# LLM Controller For BrainBot
# Created by: David Kistner (Unconditional Love)


#system imports
import os, sys, json, yaml, threading, ctypes
from pathlib import Path
from contextlib import contextmanager, redirect_stdout, redirect_stderr
from llama_cpp import Llama


# Repo-local model manifest + model folder
CURRENT_DIR = Path(__file__).resolve().parent
CORE_ROOT = CURRENT_DIR.parent
MODEL_ROOT = CORE_ROOT / "models"                 # /BrainBot/core/models
MODEL_MANIFEST = MODEL_ROOT / "manifest.yaml"     # /BrainBot/core/models/manifest.yaml


# ----------------------
# LLM Manifest Loader
# ----------------------
def load_local_llm_manifest():
    """Load the repo-local LLM manifest."""
    if not MODEL_MANIFEST.exists():
        raise FileNotFoundError(f"LLM manifest not found: {MODEL_MANIFEST}")

    with open(MODEL_MANIFEST, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    return data.get("models", {})


# ---------------------
# Suppress model noise
# ---------------------
@contextmanager
def suppress_llama_io():
    """Silence llama.cpp stdout/stderr spam during model load."""
    with open(os.devnull, "w") as devnull:
        old_stdout, old_stderr = sys.stdout, sys.stderr
        try:
            with redirect_stdout(devnull), redirect_stderr(devnull):
                yield
        finally:
            sys.stdout, sys.stderr = old_stdout, old_stderr


# =========================
# LLM CONTROLLER CLASS
# =========================
class LLMController:
    # -----------
    # Initialize
    # -----------
    def __init__(self, base_path, log=None, memory=None):
        self.base = Path(base_path)
        self.log = log or (lambda msg: print(msg))
        self.memory = memory

        # Load repo-local LLM registry
        self.models = load_local_llm_manifest()

        # Cache of loaded llama.cpp models (short-lived)
        self.loaded_models = {}

        # Track active generation threads for hard-stop
        self.active_generations = {}  # {llm_key: threading.Thread}

    # -------------------------
    # Internal: load model
    # -------------------------
    def _load_model(self, llm_key):
        if llm_key not in self.models:
            raise ValueError(f"Unknown LLM '{llm_key}' in manifest.yaml.")

        model_info = self.models[llm_key]
        model_path = MODEL_ROOT / model_info["path"]

        if not model_path.exists():
            raise FileNotFoundError(f"Model file not found: {model_path}")

        if llm_key in self.loaded_models:
            return self.loaded_models[llm_key]

        self.log(f"🧩 Loading model: {llm_key} → {model_path}")

        with suppress_llama_io():
            model = Llama(
                model_path=str(model_path),
                n_ctx=model_info.get("n_ctx", 32768),
                n_threads=model_info.get("threads", 8),
                temperature=model_info.get("temperature", 0.7),
                top_p=model_info.get("top_p", 0.9),
                top_k=model_info.get("top_k", 40),
                repeat_penalty=model_info.get("repeat_penalty", 1.1),
            )

        # Clamp context to llama.cpp max (defensive)
        try:
            ctx = model.n_ctx() if callable(model.n_ctx) else model.n_ctx
            model.n_ctx = min(ctx, 32768)
        except Exception:
            pass

        self.loaded_models[llm_key] = model
        self.log(f"✅ Model loaded: {llm_key}")
        return model

    # ------------------------------------------------------------
    # Run LLM - llama.cpp backend (single, blocking call)
    # ------------------------------------------------------------
    def _run_llm(self, prompt, llm="mistral-7b", persona=None):
        model_info = self.models.get(llm)
        if not model_info:
            raise ValueError(f"Unknown LLM '{llm}' in manifest.yaml.")

        model = self._load_model(llm)

        # Persona injection (simple identity prefix)
        if persona:
            identity = persona.get("identity", persona.get("name", "Agent"))
            prompt = f"{identity}:\n{prompt}"

        output = model(
            prompt,
            max_tokens=model_info.get("max_tokens", 512),
            stop=model_info.get("stop", ["</s>"])
        )

        return output["choices"][0]["text"].strip()

    # --------------
    # Query LLM (sync)
    # --------------
    def query(self, prompt, llm="mistral-7b", persona=None):
        """Unified query interface used by BrainBot and DialogueManager.
        Loads → generates → unloads to keep sessions fresh and memory clean.
        """
        try:
            who = persona.get("name") if isinstance(persona, dict) else "Unknown"
            self.log(f"🧠 LLM transport → llm={llm}, persona={who}")
        except Exception:
            pass

        try:
            reply = self._run_llm(prompt, llm=llm, persona=persona)
        except Exception as e:
            self.log(f"❌ LLM query failed: {e}")
            return f"⚠️ LLM error: {e}"
        finally:
            # Auto-unload after each call to avoid long-lived state
            self.unload(llm)

        return reply

# ================================
# Full session reset support
# ================================
    # -------------
    # Unload
    # -------------
    def unload(self, llm_key):
        """Unload a model from memory."""
        if llm_key in self.loaded_models:
            try:
                del self.loaded_models[llm_key]
                self.log(f"♻️ Unloaded model: {llm_key}")
            except Exception as e:
                self.log(f"⚠️ Failed to unload model {llm_key}: {e}")

    # -------------
    # Load
    # -------------
    def load(self, llm_key):
        """Force-load a model (used by DialogueManager)."""
        try:
            self._load_model(llm_key)
        except Exception as e:
            self.log(f"⚠️ Failed to load model {llm_key}: {e}")

    # -------------
    # Reset
    # -------------
    def reset(self, llm_key):
        """Reset model state by unloading + reloading."""
        self.unload(llm_key)
        self.load(llm_key)

# ================================
# Async + Hard Stop Support
# ================================
    # -------------------
    # Threaded Generate
    # -------------------
    def _threaded_generate(self, llm_key, prompt, persona):
        """Internal worker for async generation."""
        try:
            result = self._run_llm(prompt, llm=llm_key, persona=persona)
        except Exception as e:
            self.log(f"❌ Async LLM query failed: {e}")
            result = f"⚠️ LLM error: {e}"
        finally:
            # Auto-unload when done
            self.unload(llm_key)
            # Store result on controller for retrieval if desired
            setattr(self, "_last_async_result", { "llm": llm_key, "result": result })
    # -------------------
    # Async Query
    # -------------------
    def async_query(self, prompt, llm="mistral-7b", persona=None):
        """Start a non-blocking generation in a separate thread."""
        try:
            who = persona.get("name") if isinstance(persona, dict) else "Unknown"
            self.log(f"🧠 [async] LLM transport → llm={llm}, persona={who}")
        except Exception:
            pass

        t = threading.Thread(
            target=self._threaded_generate,
            args=(llm, prompt, persona),
            daemon=True
        )
        self.active_generations[llm] = t
        t.start()
        return True
    # -------------------
    # Hard Stop
    # -------------------
    def hard_stop(self, llm_key):
        """Systemic hard stop: unload model and attempt to kill active generation thread."""
        # Unload model (frees memory, clears state)
        self.unload(llm_key)

        t = self.active_generations.get(llm_key)
        if t and t.is_alive():
            try:
                # Brutal, but effective: raise SystemExit in the target thread
                res = ctypes.pythonapi.PyThreadState_SetAsyncExc(
                    ctypes.c_long(t.ident),
                    ctypes.py_object(SystemExit)
                )
                if res == 0:
                    self.log(f"⚠️ hard_stop: no thread state for {llm_key}")
                elif res > 1:
                    # Revert if we accidentally affected more than one thread
                    ctypes.pythonapi.PyThreadState_SetAsyncExc(
                        ctypes.c_long(t.ident),
                        None
                    )
                    self.log(f"⚠️ hard_stop: reverted multi-thread exception for {llm_key}")
                else:
                    self.log(f"⛔ Hard-stopped generation for {llm_key}")
            except Exception as e:
                self.log(f"⚠️ Failed to hard-stop {llm_key}: {e}")

        # Cleanup
        self.active_generations.pop(llm_key, None)


# =======================================
# DUAL AGENT CONTROLLER CLASS
# =======================================
class DualAgentController(LLMController):
    # -------------
    # Initialize
    # -------------
    def __init__(self, base_path, log=None, memory=None):
        super().__init__(base_path, log, memory)
        self.active_agents = []

    # -------------
    # Load Agents
    # -------------
    def load_agents(self, agents):
        normalized = []

        for a in agents:
            if isinstance(a, dict):
                normalized.append(a)
            elif isinstance(a, str):
                normalized.append({
                    "llm": a,
                    "name": a,
                    "identity": a,
                    "memory": None
                })
            else:
                self.log(f"⚠️ Unsupported agent type: {type(a)}")

        self.active_agents = normalized
        names = [a.get("name", str(a)) for a in normalized]
        self.log(f"🔄 Loaded agents: {', '.join(names)}")

    # -------------
    # Respond
    # -------------
    def respond(self, text):
        if not self.active_agents:
            return {"error": "⚠️ No agents loaded."}

        responses = {}

        for agent in self.active_agents:
            reply = super().query(text, llm=agent["llm"], persona=agent)
            responses[agent["name"]] = reply

            try:
                if agent.get("memory") and hasattr(agent["memory"], "store_memory"):
                    agent["memory"].store_memory(
                        content=f"Q: {text}\nA: {reply}",
                        role="conversation"
                    )
            except Exception as e:
                self.log(f"⚠️ Failed to store conversation for {agent['name']}: {e}")

        return responses

