import sounddevice as sd

print("Verfügbare Audio-Geräte:")
print(sd.query_devices())
