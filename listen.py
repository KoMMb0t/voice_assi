import time
import sounddevice as sd
import numpy as np
from openwakeword.model import Model

# --- Konfiguration ---
WAKE_WORD = "computer" # Das Wort, auf das wir hören
SAMPLE_RATE = 16000      # 16kHz, Standard für die meisten Sprachmodelle
CHUNK_SAMPLES = 1280     # 80ms Audio-Chunks (16000 * 0.080)

def main():
    """Hauptfunktion, die das Mikrofon abhört und auf das Wake Word wartet."""
    print("Initialisiere Wake-Word-Modell...")
    # Lade das vortrainierte Modell für "hey_jarvis" (kommt "computer" am nächsten)
    # openWakeWord hat kein "computer"-Modell, aber "hey jarvis" ist ein guter Startpunkt.
    # Wir können später ein eigenes Modell trainieren.
    oww_model = Model(wakeword_models=["hey_jarvis"])

    print(f"\nBereit. Höre auf das Wake Word: '{WAKE_WORD}'...")
    print("Sprich deutlich in dein Mikrofon. Drücke Strg+C zum Beenden.")

    # Callback-Funktion für den Audio-Stream
    def callback(indata, frames, time, status):
        if status:
            print(status)
        
        # Konvertiere die Audiodaten in das richtige Format
        audio_frame = np.frombuffer(indata, dtype=np.int16)

        # Füttere das Modell mit dem Audio-Frame
        prediction = oww_model.predict(audio_frame)

        # Überprüfe, ob das Wake Word erkannt wurde
        # Wir prüfen hier auf das "hey_jarvis" Modell
        if prediction["hey_jarvis"] > 0.5: # 0.5 ist der Schwellenwert
            print(f"Wake Word '{WAKE_WORD}' erkannt! Score: {prediction['hey_jarvis']:.2f}")

    try:
        # Starte den Audio-Stream vom Standard-Mikrofon
        with sd.InputStream(samplerate=SAMPLE_RATE, 
                             channels=1, 
                             dtype='int16', 
                             blocksize=CHUNK_SAMPLES, 
                             callback=callback):
            while True:
                time.sleep(1)
    except KeyboardInterrupt:
        print("\nProgramm beendet.")
    except Exception as e:
        print(f"Ein Fehler ist aufgetreten: {e}")

if __name__ == "__main__":
    main()

