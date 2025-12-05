import openwakeword

print("Starte den Download der vortrainierten Wake-Word-Modelle...")
print("Dies kann je nach Internetverbindung einen Moment dauern.")

try:
    # Diese Funktion lädt alle verfügbaren Modelle in den richtigen Ordner
    openwakeword.utils.download_models()
    print("\nDownload erfolgreich abgeschlossen!")
    print("Alle Modelle sind jetzt lokal verfügbar.")
    print("\nDu kannst jetzt das 'listen.py' Skript erneut starten.")

except Exception as e:
    print(f"\nEin Fehler beim Download ist aufgetreten: {e}")
    print("Bitte überprüfe deine Internetverbindung und versuche es erneut.")
