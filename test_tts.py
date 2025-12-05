import pyttsx3

engine = pyttsx3.init()

# Liste verfügbare Stimmen
voices = engine.getProperty('voices')
print("Verfügbare Stimmen:")
for i, voice in enumerate(voices):
    print(f"{i}: {voice.name}")

# Setze deutsche Stimme (falls verfügbar)
engine.setProperty('voice', voices[0].id)
engine.setProperty('rate', 150)
engine.setProperty('volume', 1.0)  # Volle Lautstärke

print("\nTest: Spreche jetzt...")
engine.say("Hallo, das ist ein Test der Sprachausgabe")
engine.runAndWait()
print("Fertig!")
