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

## 📦 Installation

Clone the repository:

```bash
git clone https://github.com/GlyphicMind-Solutions/BrainBot
cd BrainBot

#---install requirements---
pip install -r requirements.txt
