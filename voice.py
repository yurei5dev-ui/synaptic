import pyttsx3
import speech_recognition as sr
import sounddevice as sd
import soundfile as sf
import tempfile
import os

engine = pyttsx3.init()
engine.setProperty('rate', 175)

def speak(text):
    print(f"KAI: {text}")
    engine.say(text)
    engine.runAndWait()

def listen():
    print("Listening...")
    duration = 5
    samplerate = 16000
    recording = sd.rec(int(duration * samplerate), samplerate=samplerate, channels=1, dtype='int16')
    sd.wait()
    tmp = tempfile.mktemp(suffix=".wav")
    sf.write(tmp, recording, samplerate)
    r = sr.Recognizer()
    with sr.AudioFile(tmp) as source:
        audio = r.record(source)
    os.remove(tmp)
    try:
        text = r.recognize_google(audio)
        print(f"You: {text}")
        return text
    except:
        return ""
