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

# --- Globale Zustandsvariablen ---
wake_word_detected = False
audio_buffer = []

# --- Text-to-Speech Engine initialisieren ---
tts_engine = pyttsx3.init()
tts_engine.setProperty('rate', 150)  # Sprechgeschwindigkeit
tts_engine.setProperty('volume', 0.9)  # Lautstärke

def speak(text):
    """Spricht den gegebenen Text aus."""
    print(f"[SPEAK] {text}")
    # Kurze Pause vor dem Sprechen
    time.sleep(0.3)
    tts_engine.say(text)
    tts_engine.runAndWait()
    # Kurze Pause nach dem Sprechen
    time.sleep(0.3)


def execute_command(command_text):
    """Führt einen Befehl basierend auf dem erkannten Text aus."""
    command_lower = command_text.lower()
    
    print(f"\n[ACTION] Verarbeite Befehl: '{command_text}'")
    
    # Taschenrechner öffnen
    if "taschenrechner" in command_lower or "rechner" in command_lower:
        speak("Öffne den Taschenrechner")
        subprocess.Popen("calc.exe")
        return True
    
    # Notepad öffnen
    elif "editor" in command_lower or "notepad" in command_lower:
        speak("Öffne Notepad")
        subprocess.Popen("notepad.exe")
        return True
    
    # Browser öffnen
    elif "browser" in command_lower or "internet" in command_lower:
        speak("Öffne den Browser")
        webbrowser.open("https://www.google.com" )
        return True
    
    # YouTube öffnen
    elif "youtube" in command_lower:
        speak("Öffne YouTube")
        webbrowser.open("https://www.youtube.com" )
        return True
    
    # Datei-Explorer öffnen
    elif "explorer" in command_lower or "dateien" in command_lower:
        speak("Öffne den Datei Explorer")
        subprocess.Popen("explorer.exe")
        return True
    
    # Uhrzeit sagen
    elif "uhrzeit" in command_lower or "spät" in command_lower:
        from datetime import datetime
        now = datetime.now()
        time_str = now.strftime("%H:%M")
        speak(f"Es ist {time_str} Uhr")
        return True
    
    # Begrüßung
    elif "hallo" in command_lower or "guten morgen" in command_lower:
        speak("Hallo! Wie kann ich dir helfen?")
        return True
    
    # Unbekannter Befehl
    else:
        speak("Befehl nicht erkannt. Bitte versuche es erneut.")
        print("[ACTION] Verfügbare Befehle:")
        print("  - 'Öffne den Taschenrechner'")
        print("  - 'Öffne Notepad'")
        print("  - 'Öffne den Browser'")
        print("  - 'Öffne YouTube'")
        print("  - 'Öffne den Explorer'")
        print("  - 'Wie spät ist es?'")
        print("  - 'Hallo'")
        return False

def main():
    """Hauptfunktion des Voice Assistants."""
    global wake_word_detected, audio_buffer

    print("=== Voice Assistant mit Sprachausgabe gestartet ===")
    print("\nInitialisiere Wake-Word-Modell...")
    oww_model = Model(wakeword_models=["hey_jarvis"])

    print("Initialisiere Speech-to-Text-Modell (Vosk)...")
    vosk_model = VoskModel(lang="de")
    recognizer = KaldiRecognizer(vosk_model, SAMPLE_RATE)

    print(f"\n✓ Bereit! Höre auf das Wake Word: '{WAKE_WORD}'")
    print("✓ Drücke Strg+C zum Beenden.\n")
    
    speak("Voice Assistant bereit")

    def callback(indata, frames, time, status):
        global wake_word_detected, audio_buffer
        if status:
            print(status)
        
        audio_frame = np.frombuffer(indata, dtype=np.int16)

        if wake_word_detected:
            audio_buffer.append(bytes(audio_frame))
        else:
            prediction = oww_model.predict(audio_frame)
            if prediction["hey_jarvis"] > 0.5:
                print("\n[WAKE] Wake Word erkannt!")
                speak("Ja?")
                wake_word_detected = True
                audio_buffer = []

    with sd.InputStream(samplerate=SAMPLE_RATE, channels=1, dtype='int16', 
                        blocksize=CHUNK_SAMPLES, callback=callback):
        while True:
            if wake_word_detected:
                time.sleep(RECORD_SECONDS)

                print("[STT] Verarbeite Sprache...")
                full_audio = b''.join(audio_buffer)
                
                if recognizer.AcceptWaveform(full_audio):
                    result = json.loads(recognizer.Result())
                else:
                    result = json.loads(recognizer.FinalResult())
                
                command = result.get("text", "")
                
                if command:
                    print(f"[STT] Erkannt: \"{command}\"")
                    execute_command(command)
                else:
                    print("[STT] Konnte nichts verstehen.")
                    speak("Ich habe dich nicht verstanden")
                
                wake_word_detected = False
                audio_buffer = []
                recognizer = KaldiRecognizer(vosk_model, SAMPLE_RATE)
                print(f"\n✓ Bereit für nächsten Befehl...\n")
            
            time.sleep(0.1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        speak("Auf Wiedersehen")
        print("\n\n=== Voice Assistant beendet ===")
    except Exception as e:
        print(f"\nFehler: {e}")
