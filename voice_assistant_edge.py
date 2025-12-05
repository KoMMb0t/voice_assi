import time
import json
import subprocess
import webbrowser
import sounddevice as sd
import numpy as np
import edge_tts
import asyncio
import os
import pygame
from openwakeword.model import Model
from vosk import Model as VoskModel, KaldiRecognizer

# --- Konfiguration ---
WAKE_WORD = "hey jarvis"
SAMPLE_RATE = 16000
CHUNK_SAMPLES = 1280
SILENCE_TIMEOUT = 2.0
MAX_RECORD_TIME = 30
TTS_VOICE = "de-DE-KatjaNeural"

# Initialisiere pygame mixer
pygame.mixer.init()

async def speak_async(text):
    """Spricht Text mit Edge TTS."""
    print(f"[SPEAK] {text}")
    communicate = edge_tts.Communicate(text, TTS_VOICE)
    temp_file = "temp_speech.mp3"
    await communicate.save(temp_file)
    
    # Spiele mit pygame ab
    pygame.mixer.music.load(temp_file)
    pygame.mixer.music.play()
    
    # Warte bis Audio fertig ist
    while pygame.mixer.music.get_busy():
        time.sleep(0.1)
    
    # WICHTIG: Entlade die Datei aus pygame
    pygame.mixer.music.unload()
    
    # Lösche temporäre Datei
    try:
        time.sleep(0.3)
        os.remove(temp_file)
    except Exception as e:
        # Falls Löschen fehlschlägt, ignorieren
        pass

def speak(text):
    """Synchrone Wrapper-Funktion für speak_async."""
    asyncio.run(speak_async(text))

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
    
    elif "uhrzeit" in command_lower or "spät" in command_lower or "datum" in command_lower:
        from datetime import datetime
        now = datetime.now()
        time_str = now.strftime("%H:%M")
        speak(f"Es ist {time_str} Uhr")
    
    elif "hallo" in command_lower or "guten morgen" in command_lower:
        speak("Hallo! Wie kann ich helfen?")
    
    else:
        speak("Befehl nicht erkannt")

def listen_for_wake_word(oww_model):
    """Hört auf das Wake Word."""
    print(f"\n[LISTEN] Warte auf Wake Word '{WAKE_WORD}'...")
    
    def callback(indata, frames, time, status):
        audio_frame = np.frombuffer(indata, dtype=np.int16)
        prediction = oww_model.predict(audio_frame)
        if prediction["hey_jarvis"] > 0.95:
            callback.detected = True
            print(f"[DEBUG] Wake Word Score: {prediction['hey_jarvis']:.2f}")
    
    callback.detected = False
    
    with sd.InputStream(samplerate=SAMPLE_RATE, channels=1, dtype='int16',
                       blocksize=CHUNK_SAMPLES, callback=callback):
        while not callback.detected:
            time.sleep(0.1)
    
    time.sleep(0.5)
    return True

def record_command_with_vad(vosk_model):
    """Nimmt Audio auf bis Stille erkannt wird."""
    print(f"[RECORD] Höre zu (spreche jetzt)...")
    
    recognizer = KaldiRecognizer(vosk_model, SAMPLE_RATE)
    recognizer.SetWords(True)
    
    audio_buffer = []
    last_speech_time = time.time()
    recording_started = False
    start_time = time.time()
    
    def callback(indata, frames, time_info, status):
        nonlocal last_speech_time, recording_started
        
        audio_frame = np.frombuffer(indata, dtype=np.int16)
        audio_buffer.append(bytes(audio_frame))
        
        if recognizer.AcceptWaveform(bytes(audio_frame)):
            result = json.loads(recognizer.Result())
            if result.get("text", ""):
                last_speech_time = time.time()
                recording_started = True
                print(".", end="", flush=True)
    
    with sd.InputStream(samplerate=SAMPLE_RATE, channels=1, dtype='int16',
                       blocksize=CHUNK_SAMPLES, callback=callback):
        while True:
            current_time = time.time()
            
            if recording_started and (current_time - last_speech_time) > SILENCE_TIMEOUT:
                print("\n[RECORD] Stille erkannt - Aufnahme beendet")
                break
            
            if (current_time - start_time) > MAX_RECORD_TIME:
                print("\n[RECORD] Maximale Aufnahmezeit erreicht")
                break
            
            time.sleep(0.1)
    
    return b''.join(audio_buffer)

def main():
    """Hauptfunktion."""
    print("=== Voice Assistant mit VAD ===\n")
    
    speak("Initialisiere System")
    
    print("Lade Wake-Word-Modell...")
    oww_model = Model(wakeword_models=["hey_jarvis"])
    
    print("Lade Speech-to-Text-Modell...")
    vosk_model = VoskModel(lang="de")
    
    print("\n✓ System bereit!\n")
    speak("System bereit")
    
    try:
        while True:
            if listen_for_wake_word(oww_model):
                print("[WAKE] Wake Word erkannt!")
                
                speak("Ja?")
                
                audio_data = record_command_with_vad(vosk_model)
                
                print("[STT] Verarbeite Sprache...")
                recognizer = KaldiRecognizer(vosk_model, SAMPLE_RATE)
                
                if recognizer.AcceptWaveform(audio_data):
                    result = json.loads(recognizer.Result())
                else:
                    result = json.loads(recognizer.FinalResult())
                
                command = result.get("text", "")
                
                if command:
                    print(f"[STT] Erkannt: \"{command}\"")
                    execute_command(command)
                else:
                    print("[STT] Nichts verstanden")
                
                print("\n✓ Cooldown...")
                time.sleep(2.0)
                print("✓ Bereit")
    
    except KeyboardInterrupt:
        speak("Auf Wiedersehen")
        pygame.mixer.quit()
        print("\n\n=== Beendet ===")

if __name__ == "__main__":
    main()
