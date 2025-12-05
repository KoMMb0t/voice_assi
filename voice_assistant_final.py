import time
import json
import subprocess
import webbrowser
import sounddevice as sd
import numpy as np
import pyttsx3
from openwakeword.model import Model
from vosk import Model as VoskModel, KaldiRecognizer

# --- Konfiguration ---
WAKE_WORD = "hey jarvis"
SAMPLE_RATE = 16000
CHUNK_SAMPLES = 1280
RECORD_SECONDS = 5

# --- Text-to-Speech ---
tts_engine = pyttsx3.init()
tts_engine.setProperty('rate', 150)
tts_engine.setProperty('volume', 1.0)

def speak(text):
    """Spricht den gegebenen Text aus."""
    print(f"[SPEAK] {text}")
    tts_engine.say(text)
    tts_engine.runAndWait()

def execute_command(command_text):
    """Führt einen Befehl aus."""
    command_lower = command_text.lower()
    
    print(f"\n[ACTION] Verarbeite: '{command_text}'")
    
    if "taschenrechner" in command_lower or "rechner" in command_lower:
        speak("Öffne den Taschenrechner")
        subprocess.Popen("calc.exe")
    
    elif "editor" in command_lower or "notepad" in command_lower:
        speak("Öffne Notepad")
        subprocess.Popen("notepad.exe")
    
    elif "browser" in command_lower or "internet" in command_lower:
        speak("Öffne den Browser")
        webbrowser.open("https://www.google.com" )
    
    elif "youtube" in command_lower:
        speak("Öffne YouTube")
        webbrowser.open("https://www.youtube.com" )
    
    elif "explorer" in command_lower or "dateien" in command_lower:
        speak("Öffne den Explorer")
        subprocess.Popen("explorer.exe")
    
    elif "uhrzeit" in command_lower or "spät" in command_lower:
        from datetime import datetime
        now = datetime.now()
        time_str = now.strftime("%H:%M")
        speak(f"Es ist {time_str} Uhr")
    
    elif "hallo" in command_lower:
        speak("Hallo! Wie kann ich helfen?")
    
    else:
        speak("Befehl nicht erkannt")

def listen_for_wake_word(oww_model):
    """Hört auf das Wake Word und gibt True zurück wenn erkannt."""
    print(f"[LISTEN] Warte auf Wake Word...")
    
    def callback(indata, frames, time, status):
        audio_frame = np.frombuffer(indata, dtype=np.int16)
        prediction = oww_model.predict(audio_frame)
        if prediction["hey_jarvis"] > 0.5:
            callback.detected = True
    
    callback.detected = False
    
    with sd.InputStream(samplerate=SAMPLE_RATE, channels=1, dtype='int16',
                       blocksize=CHUNK_SAMPLES, callback=callback):
        while not callback.detected:
            time.sleep(0.1)
    
    return True

def record_command():
    """Nimmt Audio für RECORD_SECONDS Sekunden auf."""
    print(f"[RECORD] Nehme {RECORD_SECONDS} Sekunden auf...")
    audio_buffer = []
    
    def callback(indata, frames, time, status):
        audio_frame = np.frombuffer(indata, dtype=np.int16)
        audio_buffer.append(bytes(audio_frame))
    
    with sd.InputStream(samplerate=SAMPLE_RATE, channels=1, dtype='int16',
                       blocksize=CHUNK_SAMPLES, callback=callback):
        time.sleep(RECORD_SECONDS)
    
    return b''.join(audio_buffer)

def main():
    """Hauptfunktion."""
    print("=== Voice Assistant ===\n")
    
    speak("Initialisiere System")
    
    print("Lade Wake-Word-Modell...")
    oww_model = Model(wakeword_models=["hey_jarvis"])
    
    print("Lade Speech-to-Text-Modell...")
    vosk_model = VoskModel(lang="de")
    
    print("\n✓ System bereit!\n")
    speak("System bereit")
    
    try:
        while True:
            # 1. Warte auf Wake Word (Stream läuft)
            if listen_for_wake_word(oww_model):
                print("[WAKE] Wake Word erkannt!")
                
                # 2. Stream ist gestoppt - jetzt können wir sprechen
                speak("Ja?")
                
                # 3. Neuer Stream für Aufnahme
                audio_data = record_command()
                
                # 4. Stream wieder gestoppt - verarbeite Audio
                print("[STT] Verarbeite...")
                recognizer = KaldiRecognizer(vosk_model, SAMPLE_RATE)
                
                if recognizer.AcceptWaveform(audio_data):
                    result = json.loads(recognizer.Result())
                else:
                    result = json.loads(recognizer.FinalResult())
                
                command = result.get("text", "")
                
                if command:
                    print(f"[STT] Erkannt: \"{command}\"")
                    # 5. Stream gestoppt - wir können sprechen
                    execute_command(command)
                else:
                    print("[STT] Nichts verstanden")
                    speak("Ich habe nichts verstanden")
                
                print("\n✓ Bereit für nächsten Befehl\n")
    
    except KeyboardInterrupt:
        speak("Auf Wiedersehen")
        print("\n=== Beendet ===")

if __name__ == "__main__":
    main()
