import config
from groq import Groq
import ollama

def think(messages):
    if config.MODE == "groq":
        client = Groq(api_key=config.GROQ_API_KEY)
        response = client.chat.completions.create(
            model=config.GROQ_MODEL,
            messages=messages
        )
        return response.choices[0].message.content
    
    elif config.MODE == "ollama":
        response = ollama.chat(
            model=config.OLLAMA_MODEL,
            messages=messages
        )
        return response['message']['content']