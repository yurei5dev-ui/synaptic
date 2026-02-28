import json
import os
import config

MEMORY_FILE = "D:/KAI/memory/conversations.json"

def load_memory():
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, "r") as f:
            return json.load(f)
    return [{"role": "system", "content": config.KAI_PERSONALITY}]

def save_memory(messages):
    with open(MEMORY_FILE, "w") as f:
        json.dump(messages, f, indent=2)

def add_message(messages, role, content):
    messages.append({"role": role, "content": content})
    save_memory(messages)
    return messages