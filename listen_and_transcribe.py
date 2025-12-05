import time
import json
import sounddevice as sd
import numpy as np
from openwakeword.model import Model
from vosk import Model as VoskModel, KaldiRecognizer

# --- Konfiguration ---
WAKE_WORD = "hey jarvis"
SAMPLE_RATE = 16000
CHUNK_SAMPLES = 1280
RECORD_SECONDS = 5  # Wie lange nach dem Wake Word zugehört werden soll

# --- Globale Zustandsvariablen ---
wake_word_detected = False
audio_buffer = []

def main():
    """Hauptfunktion, die auf das Wake Word wartet und dann den Befehl transkribiert."""
    global wake_word_detected, audio_buffer

    print("Initialisiere Wake-Word-Modell...")
    oww_model = Model(wakeword_models=["hey_jarvis"])

    print("Initialisiere Speech-to-Text-Modell (Vosk)... (Download kann dauern)")
    # Lade ein kleines deutsches Vosk-Modell. Beim ersten Mal wird es heruntergeladen.
    vosk_model = VoskModel(lang="de")
    recognizer = KaldiRecognizer(vosk_model, SAMPLE_RATE)

    print(f"\nBereit. Höre auf das Wake Word: '{WAKE_WORD}'...")
    print("Drücke Strg+C zum Beenden.")

    # Callback-Funktion für den Audio-Stream
    def callback(indata, frames, time, status):
        global wake_word_detected, audio_buffer
        if status:
            print(status)
        
        audio_frame = np.frombuffer(indata, dtype=np.int16)

        if wake_word_detected:
            # Wenn Wake Word erkannt wurde, Audio für die Transkription sammeln
            audio_buffer.append(bytes(audio_frame))
        else:
            # Ansonsten auf Wake Word prüfen
            prediction = oww_model.predict(audio_frame)
            if prediction["hey_jarvis"] > 0.5:
                print("Wake Word erkannt! Höre jetzt auf den Befehl...")
                wake_word_detected = True
                audio_buffer = [] # Buffer für die neue Aufnahme zurücksetzen

    # Starte den Audio-Stream
    with sd.InputStream(samplerate=SAMPLE_RATE, channels=1, dtype='int16', blocksize=CHUNK_SAMPLES, callback=callback):
        while True:
            if wake_word_detected:
                # Warte die definierte Aufnahmezeit ab
                time.sleep(RECORD_SECONDS)

                # Aufnahme beenden und verarbeiten
                print("Aufnahme beendet. Verarbeite den Befehl...")
                full_audio = b''.join(audio_buffer)
                
                if recognizer.AcceptWaveform(full_audio):
                    result = json.loads(recognizer.Result())
                    command = result.get("text", "")
                    if command:
                        print(f"--> Befehl erkannt: \"{command}\"")
                    else:
                        print("Konnte nichts verstehen. Bitte versuche es erneut.")
                else:
                    # Fallback, falls AcceptWaveform nicht sofort klappt
                    result = json.loads(recognizer.FinalResult())
                    command = result.get("text", "")
                    if command:
                        print(f"--> Befehl erkannt: \"{command}\"")
                    else:
                        print("Konnte nichts verstehen. Bitte versuche es erneut.")
                
                # System zurücksetzen für das nächste Wake Word
                wake_word_detected = False
                audio_buffer = []
                print(f"\nBereit. Höre auf das Wake Word: '{WAKE_WORD}'...")
            
            time.sleep(0.1)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Ein schwerwiegender Fehler ist aufgetreten: {e}")
