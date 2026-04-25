# 🧠 BrainBot  
A deterministic, portable, local-first AI agent framework.

BrainBot is a lightweight, extensible, memory‑driven agent designed for local execution using GGUF models.  
It provides a clean architecture for running LLMs, managing persistent memory, loading personas, and executing tasks with deterministic behavior.

BrainBot is built for developers who want:
- Full control over their AI agent  
- Local execution with no cloud dependencies  
- A modular, hackable architecture  
- Deterministic behavior and reproducible outputs  
- Persona‑rich prompting and multi‑agent extensibility  

---

## ✨ Features

- **Local LLM execution** using `llama-cpp-python`  
- **Deterministic agent loop** with reproducible behavior  
- **Persistent JSON memory** (auto‑created on first run)  
- **Persona loader** for custom agent identities  
- **Model loader** with support for any `.gguf` model  
- **Simple CLI interface**  
- **Modular architecture** — easy to extend or embed  
- **Zero external dependencies** beyond Python packages  

---

## ⚠️ Issues
- **Audio features work, the code for audio output needs to just be added back into the program if you want audio functionality. (BrainBot was stripped from a much larger system)
  
- **Currently affinity is not working in the system

- **Default agents: Jesse, James (you can create new)

- **Make sure to set the mode to agents at start from the menu or you will not be able to talk to agents directly, same goes with directly communicating with the LLMs. (Know your mode)

---

## 🫡 Advice from the Creator:

-If you use a model not on the list, follow the existing manifest.yaml template and add it.
--the manifest file can be found at: /BrainBot/core/models/manifest.yaml

-You can clean the manifest.yaml file up of all your unneeded/unwanted/unowned models. What is currently there are models that I have directly tested.

-Assign custom roles from the agent.json file 
--the agent file can be found inside: /BrainBot/core/agents/"agent name"/agent.json

-Before you start, chat with the LLM directly, find a name it aligns to, create an agent with that name from the menu, go to the agents folder and assign it a custom role. Thank me later.

-You can use BrainBot to do coding tasks with the dialoge loop prompt-window, make sure your instructions are clear, and interrupt with stop dialogue when the models start to drift. You are the operator of their autonomous coding.

-The same can be said about story creation and the general creation of dialogue for games. If the model starts drifting hard, stop it reissue commands.

-The background image can be changed, rename it to background.png and replace it with the one existing in the /gui/ folder.

---

## 📦 Installation

Clone the repository:

```bash
git clone https://github.com/GlyphicMind-Solutions/BrainBot
cd BrainBot
```

#---install requirements---
```
pip install -r requirements.txt
```

== IMPORTANT ==
-The model directory is located:
/BrainBot/core/models/
*just place your LLM models in the model folder
-new models that not on the manifest.yaml, add it according to template, and drop your model in.
