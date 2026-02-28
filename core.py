import config
import think
import memory
import voice
import threading

def run():
    voice.speak(f"Hey, I'm {config.KAI_NAME}. What's up?")
    messages = memory.load_memory()
    
    print("\nType your message OR press Enter to use voice\n")
    
    while True:
        user_input = input("You (type or press Enter for voice): ").strip()
        
        if user_input == "":
            user_input = voice.listen()
            if not user_input:
                continue
        
        if "quit" in user_input.lower() or "bye" in user_input.lower():
            voice.speak("Later!")
            break
        
        messages = memory.add_message(messages, "user", user_input)
        response = think.think(messages)
        messages = memory.add_message(messages, "assistant", response)
        
        voice.speak(response)

if __name__ == "__main__":
    run()