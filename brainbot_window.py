# /BrainBot/brainbot_window.py
# BrainBot Desktop Window - GUI
# Created by: David Kistner (Unconditional Love)



# system imports
import sys, threading, time, json, os, psutil, yaml
from datetime import datetime
from pathlib import Path
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QTextEdit, QLineEdit, QMenuBar, QMenu, QAction,
    QDockWidget, QVBoxLayout, QInputDialog, QDialog, QVBoxLayout, QDialogButtonBox, QLabel,
    QCheckBox, QFileDialog, QTabWidget
)

# folder imports
from core.memory.memorycore import MemoryCore
from core.dialogue.dialoguemanager import DialogueManager

#pathing
CURRENT_DIR = Path(__file__).resolve().parent   #Current Directory
BRAINBOT_ROOT = CURRENT_DIR   #brainbot root = current directory
sys.path.append(str(BRAINBOT_ROOT))   #brainbot root
BASE_PATH = BRAINBOT_ROOT   #base path = brainbot root = current directory
SYSTEM_MIND_MANIFEST = BASE_PATH / "core" / "models" / "manifest.yaml" #manifest path


# ======================================
# AFFINITY CORE SELECTION DIALOG CLASS
# ======================================
class CoreSelectionDialog(QDialog):
    """
        Affinity Core Selection Dialog Box
        -sets CPU cores for LLMs/Agents
    """
    # ---------------------------
    # Initialize
    # ---------------------------
    def __init__(self, cores, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Assign CPU Cores")
        self.selected_cores = []
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Select cores for this agent:"))
        self.checkboxes = []

        for c in cores:
            cb = QCheckBox(f"Core {c}")
            layout.addWidget(cb)
            self.checkboxes.append((c, cb))

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
    # -------------------------
    # Affinity Core Selection
    # -------------------------
    def get_selected(self):
        return [c for c, cb in self.checkboxes if cb.isChecked()]


# =================================
# LARGE PROMPT DIALOG CLASS
# =================================
class LargePromptDialog(QDialog):
    """
        Dialogue Loop Prompt Window
        - sets agents topic, directives, and instruction
        - now supports Save / Load / Run Dialogue
    """
    # ------------
    # Initialize
    # ------------
    def __init__(self, title="Dialogue Seed", parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumSize(700, 500)

        self.parent_window = parent  # BrainBotWindow reference

        layout = QVBoxLayout(self)

        label = QLabel("Enter the initial topic or full instructions for both agents:")
        layout.addWidget(label)

        self.text_edit = QTextEdit()
        self.text_edit.setStyleSheet(
            "background-color: rgba(0,0,0,180); color: cyan; font-family: monospace;"
        )
        layout.addWidget(self.text_edit)

        # Pre-fill template
        self.text_edit.setPlainText(
            "### Scenario / Context\n"
            "\n"
            "Describe the situation the agents are entering.\n"
            "\n"
            "### Agent A Instructions\n"
            "- Goals:\n"
            "- Constraints:\n"
            "- Style:\n"
            "\n"
            "### Agent B Instructions\n"
            "- Goals:\n"
            "- Constraints:\n"
            "- Style:\n"
            "\n"
            "### Starting Topic / Question\n"
            "..."
        )
        #--Buttons: Save, Load, Run, Cancel--#
        buttons = QDialogButtonBox()
        #Save Prompt button
        self.btn_save = buttons.addButton("Save Prompt", QDialogButtonBox.ActionRole)
        #Load Prompt button
        self.btn_load = buttons.addButton("Load Prompt", QDialogButtonBox.ActionRole)
        #Start Dialogue button
        self.btn_run = buttons.addButton("Start Dialogue", QDialogButtonBox.AcceptRole)
        #Cancel button
        self.btn_cancel = buttons.addButton(QDialogButtonBox.Cancel)
        #On Click Action
        self.btn_save.clicked.connect(self.save_prompt)
        self.btn_load.clicked.connect(self.load_prompt)
        self.btn_run.clicked.connect(self.accept)
        self.btn_cancel.clicked.connect(self.reject)

        layout.addWidget(buttons)
    # -----------
    # Get Text
    # -----------
    def get_text(self):
        return self.text_edit.toPlainText().strip()
    # -------------------------
    # Save Prompt
    # -------------------------
    def save_prompt(self):
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Prompt",
            "",
            "Text Files (*.txt);;Markdown (*.md);;All Files (*)"
        )
        if not path:
            return
        with open(path, "w", encoding="utf-8") as f:
            f.write(self.get_text())
    # -------------------------
    # Load Prompt
    # -------------------------
    def load_prompt(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Load Prompt",
            "",
            "Text Files (*.txt *.md);;All Files (*)"
        )
        if not path:
            return
        with open(path, "r", encoding="utf-8") as f:
            self.text_edit.setPlainText(f.read())


# ================================
# BRAINBOT WINDOW CLASS
# ================================
class BrainBotWindow(QMainWindow):
    """ BrainBot Window
        - Handles Agent Creation,
        - Chat Functionality
        - Voice Tuning
        - Minor scan/learn functionality
   """
    # -------------------
    # Initialize
    # -------------------
    def __init__(self, root=BASE_PATH, log_fn=None):
        self.root = Path(root)
        self.log = log_fn or print
        super().__init__()
        print("🧠 Initializing BrainBotWindow...")
        self.setWindowTitle("BrainBot Interface")
        self.setGeometry(100, 100, 1200, 800)

        # Central widget
        central = QWidget(self)
        self.setCentralWidget(central)
        central_layout = QVBoxLayout(central)
        central.setLayout(central_layout)

        # Background // can be changed
        bg_path = f"{BASE_PATH}/gui/background.png"
        self.setStyleSheet(f"""
            QMainWindow {{
                background-image: url({bg_path});
                background-repeat: no-repeat;
                background-position: center;
                background-attachment: fixed;
            }}
        """)

        # Menu bar
        self.menu_bar = QMenuBar(self)
        self.setMenuBar(self.menu_bar)
        self.menu_bar.setStyleSheet("background-color: black; color: white; font-size: 13px;")

        # Identity // neutral defaults for public use
        self.user_name = "User"
        self.user_identity = "Guest"

        # Active Agents Voice
        self.active_agents = []
        self.active_llms = []
        self.voice_enabled = False
        self.last_user_input_time = time.time()
        self.pending_clarification_agent = None

        # LLM manifest (local manifest.yaml)
        self.llm_manifest = self.load_llm_manifest()

        # Status timer
        self.status_timer = QTimer(self)
        self.status_timer.timeout.connect(self.update_user_status)
        self.status_timer.start(10000)

        # System menu
        system_menu = QMenu("🖥️ System", self)
        system_menu.addAction(QAction("Shutdown", self, triggered=lambda: QApplication.quit()))
        self.menu_bar.addMenu(system_menu)

        # Agent Menu
        agents_menu = QMenu("👥 Agents", self)
        agents_menu.addAction(QAction("Load Agent (Folder)", self, triggered=self.prompt_load_agent_folder))
        agents_menu.addAction(QAction("Create Agent Folder", self, triggered=self.prompt_create_agent_folder))
        agents_menu.addAction(QAction("Unload Agent", self, triggered=self.prompt_unload_agent))
        agents_menu.addAction(QAction("List Active Agents", self, triggered=self.update_status_panel))
        self.menu_bar.addMenu(agents_menu)

        # LLM menu (manifest-driven)
        llm_menu = QMenu("🧩 LLM", self)
        if self.llm_manifest:
            for llm_name in self.llm_manifest.keys():
                llm_menu.addAction(QAction(
                    llm_name,
                    self,
                    triggered=lambda checked, key=llm_name: self.set_llm(key)
                ))
        else:
            for llm in self.active_llms:
                llm_menu.addAction(QAction(
                    llm,
                    self,
                    triggered=lambda checked, key=llm: self.set_llm(key)
                ))

        unload_llm_menu = QMenu("Unload LLM", self)
        unload_llm_menu.addAction(QAction("Remove Active LLM", self, triggered=self.prompt_unload_llm))
        llm_menu.addMenu(unload_llm_menu)
        self.menu_bar.addMenu(llm_menu)

        # Toggles menu
        toggles_menu = QMenu("⚙️ Toggles", self)
        self.senses_toggle = QAction("Senses", self, checkable=True)
        toggles_menu.addActions([
            self.senses_toggle,
        ])
        self.menu_bar.addMenu(toggles_menu)

        # Voice
        voice_menu = QMenu("🎙️ Voice", self)
        voice_menu.addAction(QAction("Tune Agent Voice", self, triggered=self.prompt_tune_voice))
        audio_in_toggle = QAction("Audio Input", self, checkable=True)
        audio_out_toggle = QAction("Audio Output", self, checkable=True)
        audio_in_toggle.triggered.connect(lambda checked: self.brain.toggle_audio_input(checked) if self.brain else None)
        audio_out_toggle.triggered.connect(lambda checked: self.brain.toggle_audio_output(checked) if self.brain else None)
        toggles_menu.addAction(audio_in_toggle)
        toggles_menu.addAction(audio_out_toggle)
        self.menu_bar.addMenu(voice_menu)

        # Dialogue menu
        dialogue_menu = QMenu("🗣️ Dialogue", self)

        # Start 2-Agent Dialogue
        dialogue_menu.addAction(QAction("Start Dialogue (2 Agents)", self,
            triggered=lambda: self._start_dual_dialogue()
        ))
        # Stop Dialogue
        dialogue_menu.addAction(QAction("Stop Dialogue", self,
            triggered=lambda: (
                self.dialogue_manager.stop()
                if hasattr(self, "dialogue_manager")
                else self.chat("⚠️ DialogueManager not ready.", agent_name="System")
            )
        ))
        self.menu_bar.addMenu(dialogue_menu)

        # Chat dock
        self.chat_window = QTextEdit()
        self.chat_window.setReadOnly(True)
        self.chat_window.setStyleSheet("background-color: rgba(0,0,0,160); color: white;")
        self.chat_dock = QDockWidget("Chat", self)
        self.chat_dock.setWidget(self.chat_window)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.chat_dock)

        # Status indicator
        self.status_action = QAction("🟢 User Active", self)
        self.status_action.setEnabled(False)

        # Log dock
        self.log_status_tabs = QTabWidget()
        self.log_window = QTextEdit()
        self.log_window.setReadOnly(True)
        self.log_window.setStyleSheet("background-color: rgba(0,0,0,160); color: orange;")
        self.log_status_tabs.addTab(self.log_window, "Log")

        # Status dock
        self.status_window = QTextEdit()
        self.status_window.setReadOnly(True)
        self.status_window.setStyleSheet("background-color: rgba(0,0,0,160); color: lightgreen;")
        self.log_status_tabs.addTab(self.status_window, "Status")
        self.log_dock = QDockWidget("Log / Status", self)
        self.log_dock.setWidget(self.log_status_tabs)
        self.addDockWidget(Qt.RightDockWidgetArea, self.log_dock)

        # Input dock
        self.input_field = QLineEdit()
        self.input_field.returnPressed.connect(self.handle_input)
        self.input_field.setStyleSheet("background-color: rgba(0,0,0,200); color: cyan;")
        self.input_dock = QDockWidget("Input", self)
        self.input_dock.setWidget(self.input_field)
        self.addDockWidget(Qt.BottomDockWidgetArea, self.input_dock)

        # Chat mode
        self.chat_mode = "Agents"
        modes_menu = QMenu("🧭 Mode", self)
        modes_menu.addAction(QAction("LLM Direct", self, triggered=lambda: self.set_chat_mode("llm_direct")))
        modes_menu.addAction(QAction("Agents", self, triggered=lambda: self.set_chat_mode("agents")))
        self.menu_bar.addMenu(modes_menu)

        # Timer to update deep scan progress
        self.deep_scan_timer = QTimer(self)
        self.deep_scan_timer.start(2000)

        # Runtime state
        try:
            from core.brainbot import BrainBot
            self.brain = BrainBot(
                base_path=BASE_PATH,
                log=self.log
            )
            self.chat("🧠 BrainBot core initialized.", agent_name="System")

            # Initialize DialogueManager immediately
            self.dialogue_manager = DialogueManager(
                self.brain.llm,
                self.chat,
                self.log,
                speak_fn=self._speak_agent
            )
            self.log("✅ DialogueManager initialized")

        except Exception as e:
            self.log(f"⚠️ Failed to initialize BrainBot: {e}")
            self.brain = None

        print("✅ BrainBotWindow initialized w/ BrainBot.")

# ============================
# LLM Functionality
# ============================
    # -------------------------
    # LLM manifest loader
    # -------------------------
    def load_llm_manifest(self):
        try:
            if not SYSTEM_MIND_MANIFEST.exists():
                print(f"⚠️ LLM manifest not found at {SYSTEM_MIND_MANIFEST}")
                return {}
            with open(SYSTEM_MIND_MANIFEST, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
            models = data.get("models", {})
            print(f"✅ Loaded {len(models)} LLMs from local manifest.yaml.")
            return models
        except Exception as e:
            print(f"⚠️ Failed to load LLM manifest: {e}")
            return {}

    # -------------------------
    # Set LLM
    # -------------------------
    def set_llm(self, backend_key):
        if backend_key not in self.active_llms:
            self.active_llms.append(backend_key)
            self.chat(f"🔄 Added LLM backend {backend_key}", agent_name="System")
        else:
            self.chat(f"⚠️ LLM {backend_key} already active.", agent_name="System")
        self.update_status_panel()

    # ------------------------
    # Unload LLM
    # ------------------------
    def prompt_unload_llm(self):
        if not self.active_llms:
            self.chat("⚠️ No active LLMs to unload.", agent_name="System")
            return

        choice, ok = QInputDialog.getItem(
            self,
            "Unload LLM",
            "Choose LLM to unload:",
            self.active_llms,
            0,
            False
        )

        if not ok or not choice:
            return

        removed_agents = []

        for agent in list(self.active_agents):
            if agent["llm"] == choice:
                if "cores" in agent:
                    try:
                        p = psutil.Process()
                        p.cpu_affinity(agent["cores"])
                        self.log(f"🔓 Freed CPU cores {agent['cores']} from {agent['name']}")
                    except Exception as e:
                        self.log(f"⚠️ Failed to reset affinity for {agent['name']}: {e}")

                self.active_agents.remove(agent)
                removed_agents.append(agent["name"])

        self.active_llms = [llm for llm in self.active_llms if llm != choice]
        msg = f"🗑️ LLM unloaded: {choice}"

        if removed_agents:
            msg += f" (agents removed: {', '.join(removed_agents)})"
        self.chat(msg, agent_name="System")
        self.update_status_panel()

# ==================================================
# Agent Functionality
# ==================================================
    # ----------------------------------
    # Load Agent (folder-based persona)
    # ----------------------------------
    def prompt_load_agent_folder(self):
        default_dir = BASE_PATH / "core" / "agents"
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Agent Directory",
            str(default_dir)
        )

        if not folder:
            return

        agent_dir = Path(folder)
        json_files = [f for f in agent_dir.glob("*.json") if f.name.lower() != "questions.json"]

        if not json_files:
            self.chat("⚠️ No persona .json file found in selected directory.", agent_name="System")
            return

        if len(json_files) > 1:
            choices = [f.name for f in json_files]
            choice, ok = QInputDialog.getItem(self, "Select Agent File", "Choose agent file:", choices, 0, False)
            if not ok or not choice:
                return
            agent_json = agent_dir / choice
        else:
            agent_json = json_files[0]

        # Load persona JSON
        with open(agent_json, "r", encoding="utf-8") as f:
            agent_data = json.load(f)

        if not isinstance(agent_data, dict):
            self.chat("⚠️ Selected JSON is not a valid agent persona file.", agent_name="System")
            return

        # Ensure questions.json exists
        questions_file = agent_dir / "questions.json"
        if not questions_file.exists():
            with open(questions_file, "w", encoding="utf-8") as qf:
                json.dump([], qf, indent=2)

        # CPU core selection
        available_cores = list(range(psutil.cpu_count()))
        dlg = CoreSelectionDialog(available_cores, self)

        if dlg.exec_() == QDialog.Accepted:
            selected_cores = dlg.get_selected()
        else:
            return

        # Must have at least one active LLM
        if not self.active_llms:
            self.chat("⚠️ No active LLMs available. Please add one first.", agent_name="System")
            return

        # Choose LLM backend
        llm_choice, ok = QInputDialog.getItem(
            self, "Assign LLM", "Choose LLM backend:", self.active_llms, 0, False
        )

        if not ok or not llm_choice:
            return

        # Agent name
        agent_name = agent_data.get("name", agent_json.stem)

        # Load MemoryCore from local agents root
        memory = MemoryCore(
            base_path=str(default_dir),
            agent_name=agent_name,
            log=self.log
        )

        agent_root = memory.agent_dir

        # Build agent context for DialogueManager
        agent_context = {
            "name": agent_name,
            "llm": llm_choice,
            "identity": agent_data.get("identity", agent_name),

            # MemoryCore (agent.json)
            "memory": memory,
            "agent_data": memory.agent_data,

            # CPU affinity
            "cores": selected_cores,
        }

        # Register agent
        self.active_agents.append(agent_context)

        self.chat(
            f"✅ Agent loaded: {agent_context['name']} "
            f"(LLM={llm_choice}, cores={selected_cores}, file={agent_json.name})",
            agent_name="System"
        )

        self.update_status_panel()
    # ----------------
    # Unload Agent
    # ----------------
    def prompt_unload_agent(self):
        if not self.active_agents:
            self.chat("⚠️ No agents loaded.", agent_name="System")
            return

        names = [a["name"] for a in self.active_agents]
        choice, ok = QInputDialog.getItem(
            self,
            "Unload Agent",
            "Choose agent to unload:",
            names,
            0,
            False
        )

        if not ok or not choice:
            return

        for agent in list(self.active_agents):
            if agent["name"] == choice:
                self.active_agents.remove(agent)
                self.chat(f"🗑️ Agent unloaded: {choice}", agent_name="System")
                break

        self.update_status_panel()
    # --------------------------
    # Create Agent Folder
    # --------------------------
    def prompt_create_agent_folder(self):
        name, ok = QInputDialog.getText(self, "Create Agent Folder", "Enter agent name:")

        if not ok or not name.strip():
            return

        agent_dir = Path(BASE_PATH) / "core" / "agents" / name.strip()
        agent_dir.mkdir(parents=True, exist_ok=True)
        (agent_dir / "avatar").mkdir(exist_ok=True)
        (agent_dir / "voice").mkdir(exist_ok=True)
        (agent_dir / "files").mkdir(exist_ok=True)

        agent_json = agent_dir / "agent.json"
        if not agent_json.exists():
            with open(agent_json, "w", encoding="utf-8") as f:
                json.dump({
                    "name": name.strip(),
                    "identity": name.strip(),
                    "role": name.strip(),
                    "personality": name.strip(),
                    "events": [],
                    "memory": [],
                }, f, indent=2)

        self.chat(f"🆕 Agent folder created: {name.strip()}", agent_name="System")
    # ------------------------------
    # Create general Agent details
    # ------------------------------
    def prompt_create_agent(self):
        selector = StyleSelector(base_path=BASE_PATH, log=self.log)

        name, ok = QInputDialog.getText(self, "Create Agent", "Enter agent name:")
        if not ok or not name.strip():
            return

        voice, ok = QInputDialog.getText(self, "Create Agent", "Enter voice (e.g., female-soft, male-deep):")
        if not ok:
            return

        role, ok = QInputDialog.getText(self, "Create Agent", "Enter role (e.g., Guide, Archivist):")
        if not ok:
            return

        personality, ok = QInputDialog.getMultiLineText(self, "Create Agent", "Enter personality description:")
        if not ok:
            return

        agent = selector.create_agent(
            name=name.strip(),
            voice=voice.strip(),
            role=role.strip(),
            personality=personality.strip(),
            style_flags={"poetic_mode": 0, "prefers_step": 0}
        )

        out_path = selector.save_agent(agent)
        self.chat(f"🆕 Agent created: {agent['name']}", agent_name="System")
        self.log(f"💾 Agent persona saved at {out_path}")

# =========================
# Chat Functionality
# =========================
    # ---------------
    # Set Chat Mode
    # ---------------
    def set_chat_mode(self, mode):
        self.chat_mode = mode
        self.chat(f"🔀 Chat mode set to {mode}", agent_name="System")
        self.update_status_panel()
    # ---------------
    # Chat
    # ---------------
    def chat(self, message, agent_name=None):
        if agent_name is None:
            agent_name = "BrainBot"

        if agent_name == self.user_name:
            name_color = "red"
            text_color = "yellow"
        elif agent_name == "BrainBot":
            name_color = "orange"
            text_color = "gold"
        else:
            slot_colors = {
                1: "blue",
                2: "purple",
                3: "orange",
                4: "green",
                5: "yellow",
                6: "gold"
            }
            idx = None
            for i, a in enumerate(self.active_agents, start=1):
                if a["name"] == agent_name:
                    idx = i
                    break
            name_color = slot_colors.get(idx, "white")
            text_color = "white"

        formatted = (
            f"<span style='color:{name_color};'><b>{agent_name}:</b></span>"
            f"<pre style='color:{text_color}; white-space: pre-wrap; "
            f"font-family: monospace; margin: 4px 0 12px 0;'>{message}</pre>"
        )

        self.chat_window.append(formatted)
    # -------------------------
    # Input handling
    # -------------------------
    def handle_input(self):
        text = self.input_field.text().strip()
        self.input_field.clear()
        self.last_user_input_time = time.time()

        if not text:
            return

        # If dual-agent dialogue is running → interrupt
        if hasattr(self, "dialogue_manager") and getattr(self.dialogue_manager, "_running", False):
            self.dialogue_manager.user_interrupt(text)
            return

        # Otherwise follow normal chat modes
        if not self.brain:
            self.chat("⚠️ BrainBot not loaded.", agent_name="System")
            return

        elif self.chat_mode == "agents":
            if not self.active_agents:
                self.chat("⚠️ No agents loaded.", agent_name="System")
                return

            self.chat(text, agent_name=self.user_name)

            agent = self.active_agents[0]
            reply = self.brain.llm.query(
                text,
                llm=agent["llm"],
                persona=agent
            )
            self.chat(reply, agent_name=agent["name"])

        elif self.chat_mode == "llm_direct":
            if not self.active_llms:
                self.chat("⚠️ No active LLMs available.", agent_name="System")
                return

            llm_key = self.active_llms[0]
            reply = self.brain.llm.query(text, llm=llm_key, persona=None)
            self.chat(reply, agent_name=f"LLM:{llm_key}")
    # -------------------------------
    # Dual Agent Dialogue
    # -------------------------------
    def _start_dual_dialogue(self):
        if not hasattr(self, "dialogue_manager"):
            self.chat("⚠️ DialogueManager not initialized.", agent_name="System")
            return

        if len(self.active_agents) < 2:
            self.chat("⚠️ Need at least 2 agents loaded.", agent_name="System")
            return

        # Select which two agents to use
        names = [a["name"] for a in self.active_agents]
        a_name, ok1 = QInputDialog.getItem(self, "Select Agent A", "Choose first agent:", names, 0, False)
        if not ok1:
            return

        b_name, ok2 = QInputDialog.getItem(self, "Select Agent B", "Choose second agent:", names, 1, False)
        if not ok2 or b_name == a_name:
            self.chat("⚠️ Must choose two different agents.", agent_name="System")
            return

        agent_a = next(a for a in self.active_agents if a["name"] == a_name)
        agent_b = next(a for a in self.active_agents if a["name"] == b_name)

        # Large prompt dialog
        dlg = LargePromptDialog("Dialogue Seed", self)
        if dlg.exec_() != QDialog.Accepted:
            return

        seed = dlg.get_text()
        if not seed:
            self.chat("⚠️ Seed text cannot be empty.", agent_name="System")
            return

        # Start continuous loop
        self.dialogue_manager.start_dual(agent_a, agent_b, seed.strip())


# ===========================
# Voice Functionality
# ===========================
    # -------------
    # Tune Voice
    # --------------
    def prompt_tune_voice(self):
        if not self.brain:
            self.chat("⚠️ BrainBot not loaded.", agent_name="System")
            return

        filepath, _ = QFileDialog.getOpenFileName(self, "Select Voice Sample", "", "Audio Files (*.mp3 *.wav)")

        if not filepath:
            return

        if not self.active_agents:
            self.chat("⚠️ No agent loaded.", agent_name="System")
            return

        agent = self.active_agents[0]
        msg = self.brain.tune_agent_voice(agent["name"], filepath)
        self.chat(msg, agent_name="System")
    # -------------------------
    # Voice output
    # -------------------------
    def _speak_agent(self, agent_context, text):
        if not self.brain or not getattr(self.brain, "audio_output_enabled", False):
            return

        try:
            self.brain.senses.audio.synthesize_speech(text, agent=agent_context)
        except Exception as e:
            self.log(f"⚠️ Failed to speak for {agent_context.get('name','Agent')}: {e}")

# ============================
# Status / Log Functionality
# ============================
    # -------------------------
    # Log
    # -------------------------
    def log(self, message):
        timestamp = datetime.utcnow().strftime("%H:%M:%S")
        formatted = f"[{timestamp}] {message}"
        QTimer.singleShot(0, lambda: self.log_window.append(formatted))
    # ---------------------
    # Status Panel Updater
    # ---------------------
    def update_status_panel(self):
        self.status_window.clear()

        if self.active_agents:
            agent_lines = []
            for i, a in enumerate(self.active_agents, start=1):
                color = "cyan"
                marker = "⚡"
                agent_lines.append(
                    f"<span style='color:{color};'>{marker} {a['name']} (LLM={a['llm']})</span>"
                )
            agent_info = "; ".join(agent_lines)
        else:
            agent_info = "None"

        lines = [
            f"Active LLMs: {', '.join(self.active_llms) if self.active_llms else 'None'}",
            f"Active agents: {agent_info}",
            f"<span style='color:orange;'>User: {self.user_name}</span>",
            f"<span style='color:orange;'>User identity: {self.user_identity}</span>",
            f"Mode: {'Voice' if self.voice_enabled else 'Text-Only'}",
            f"Status: {self.status_action.text()}"
        ]

        self.status_window.append("<b>Status Panel</b>")
        self.status_window.append("<br>".join(lines))
    # ---------------------
    # User Status Update
    # ---------------------
    def update_user_status(self):
        if (time.time() - self.last_user_input_time) > 240:
            self.status_action.setText("🔴 Away Mode")
        else:
            self.status_action.setText("🟢 User Active")


# =============================
# Window Initializer
# =============================
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = BrainBotWindow()
    window.show()
    sys.exit(app.exec_())

