# BrainBot
### A Deterministic Multi‑Agent LLM Runtime  
Posted by: **David Kistner (Unconditional Love)**
- This version is gutted from the GlyphOS+ version
- Created by GlyphicMind Solutions LLC.

BrainBot is a portable, deterministic, multi‑agent system designed for:
- persona‑rich agent dialogue  
- reproducible task execution  
- isolated LLM sessions  
- local model loading via llama.cpp  
- optional audio input/output  

BrainBot does **not** rely on cloud APIs.  
All models run locally using `.gguf` files.

---

## 🔧 Features

### ✔️ Multi‑Agent Dialogue Loop
Two agents communicate in alternating turns using:
- persona‑rich prompts  
- isolated model sessions  
- unload → load → reset cycles  
- memory + event tracking  

### ✔️ Local LLM Execution
BrainBot uses `llama-cpp-python` to load `.gguf` models from:
/BrainBot/core/models/


### Directions
1. install dependencies from requirements.txt
2. put your LLM in /BrainBot/core/models/
3. there is a manifest.yaml file inside the models folder, check to see if your model isnt already listed, if it is run the program
4. add an entry to manifest.yaml file to add your LLM .gguf file (most huggingface.co models come with one for the model you downloaded)
5. entry point is brainbot_window.py // open a terminal or command prompt to the BrainBot folder and do a python3 brainbot_window.py
---------------------------
6. use the LLM menu to load your model
7. Create an agent with the agents menu
8. load the agent from the agents menu
9. from the mode menu, select agents (from there you can chat with your agent, or agents)
10. Dialogue Loop - create 2 agents and tie them each to an LLM
11. start dialogue loop with a topic
----------------------------

12. Enjoy


### Suggestions

utilize the dialogue loop to code, write stories or just get tasks done. The more specific you are about the topic, the better.

### Disclaimer

some models can be quite big, and do take time to generate the response, especially durring the dialogue loop, keep in mind that
it may take some time for actual work to progress. generating responses locally is not the same as generating responses on a
cloud server.

