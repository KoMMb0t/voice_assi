# Voice Assistant - Refactored Version

Ein professionell refaktorierter sprachgesteuerter Assistent für Windows mit robuster State Machine, modularer Architektur und erweiterbarem Command Pattern.

## 🚀 Quick Start

### Installation
```bash
# Dependencies installieren
pip install -r requirements.txt

# Modelle herunterladen (falls nicht vorhanden)
python download_models.py
```

### Starten
```bash
python main.py
```

## 📁 Dateienstruktur

```
├── main.py                          # Haupteinstiegspunkt (VoiceAssistant Orchestrator)
├── config.py                        # Konfigurationsmanagement (Singleton)
├── config.yaml                      # Konfigurationsdatei
├── state_machine.py                 # State Machine + Event System
├── components.py                    # Audio, WakeWord, STT, TTS Komponenten
├── commands.py                      # Command Pattern Implementierung
├── logger_setup.py                  # Logging-Konfiguration
├── REFACTORING_NOTES.md             # Umfangreiche Dokumentation
├── requirements.txt                 # Python Dependencies
├── voice_assistant_edge_ultimate.py # Alter Code (noch vorhanden)
└── README.md                        # Diese Datei
```

## 🏗️ Architektur

### State Machine
```
IDLE ──→ LISTENING_FOR_COMMAND ──→ PROCESSING_COMMAND ──→ SPEAKING ──→ COOLDOWN ──→ IDLE
```

### Komponenten
- **VoiceAssistant**: Hauptorchestrator
- **AudioProcessor**: Audio-Input-Management
- **WakeWordDetector**: OpenWakeWord Integration
- **SpeechToTextConverter**: Vosk STT
- **TextToSpeechEngine**: Edge TTS
- **CommandRegistry**: Command Pattern Management

## ⚙️ Konfiguration

Konfiguriere in `config.yaml`:

```yaml
audio:
  sample_rate: 16000
  chunk_samples: 1280
  device_index: null              # null = Default Device

wake_word:
  model_name: hey_jarvis
  threshold: 0.5                  # Erhöhen = weniger sensitiv
  cooldown_seconds: 4.0           # Nach Erkennung pausieren
  buffer_clear_chunks: 15         # Puffer-Clearing

speech_recognition:
  model_language: de
  silence_timeout: 2.0
  max_record_time: 30

text_to_speech:
  voice: de-DE-KatjaNeural

logging:
  level: INFO                     # DEBUG, INFO, WARNING, ERROR
  file: voice_assistant.log
```

## 🎯 Verwendung

### Wake Word aktivieren
Sagen Sie "Hey Jarvis"

### Befehle
- **Taschenrechner**: "Öffne den Taschenrechner"
- **Notepad**: "Öffne Notepad"
- **Explorer**: "Öffne den Explorer"
- **Firefox**: "Öffne Firefox"
- **ChatGPT**: "Öffne ChatGPT"
- **Uhrzeit**: "Wie spät ist es?" oder "Uhrzeit"
- **Datum**: "Welcher Tag ist heute?" oder "Datum"
- **Hilfe**: "Hilfe" oder "Was kannst du?"

### Befehl abbrechen
- "Danke"
- "Abbrechen"
- "Stopp"
- "Vergiss es"

## 🔧 Neuen Befehl hinzufügen

```python
# In commands.py
class MyCommand(BaseCommand):
    def __init__(self):
        super().__init__(
            name="mycommand",
            description="My custom command",
            command_type=CommandType.SYSTEM,
            keywords=["keyword1", "keyword2"]
        )
    
    def matches(self, text: str) -> bool:
        return any(kw in text.lower() for kw in self.keywords)
    
    def execute(self) -> str:
        # Logic here
        self.log_execution()
        return "Command response"

# Registrieren in CommandRegistry._load_default_commands()
self.commands.append(MyCommand())
```

## 🐛 Troubleshooting

### Wake-Word wird nicht erkannt
→ `config.yaml`: `threshold` senken (z.B. 0.3)

### Wake-Word wird doppelt erkannt
→ `config.yaml`: `cooldown_seconds` erhöhen (z.B. 5.0)

### Befehle werden nicht erkannt
→ `config.yaml`: `silence_timeout` erhöhen (z.B. 3.0)

### Debug-Logging aktivieren
→ `config.yaml`: `logging.level` auf `DEBUG` setzen

### Log-Datei anschauen
```bash
tail -f voice_assistant.log
```

## 📚 Dokumentation

**Für umfassende Dokumentation siehe `REFACTORING_NOTES.md`**

- Detaillierte Architekturübersicht
- Design Patterns Erklärung
- Komponenten-Dokumentation
- Erweiterbarkeitsleitfaden
- Performance-Tipps

## 🎨 Verbesserungen gegenüber Originalcode

| Feature | Alt | Neu |
|---------|-----|-----|
| Architektur | Prozedural | OOP + State Machine |
| Doppel-Detection | ❌ Problematisch | ✅ Verhindert |
| Fehlerbehandlung | Basic | Robust |
| Erweiterbarkeit | Schwierig | Einfach (Command Pattern) |
| Logging | print() | Strukturiert |
| Dokumentation | ❌ Keine | ✅ Umfangreich |
| Type Hints | ❌ Keine | ✅ Vollständig |
| Testbarkeit | ❌ Schwierig | ✅ Modular |
| Wartbarkeit | Niedrig | ⭐⭐⭐⭐⭐ Sehr hoch |

## 💡 Design Patterns

- **State Machine**: Robuste Zustandsverwaltung
- **Command Pattern**: Erweiterbare Befehle
- **Singleton**: Config & Logger
- **Dependency Injection**: Flexible Komponenten
- **Observer**: Event-basierte Kommunikation

## 📝 Logging

Alle Aktionen werden in `voice_assistant.log` protokolliert:

```
2025-12-06 12:00:00,123 - state_machine - INFO - State transition: IDLE -> LISTENING_FOR_COMMAND
2025-12-06 12:00:01,456 - components - INFO - Wake word detected with confidence: 0.75
2025-12-06 12:00:02,789 - commands - INFO - Command executed: calculator
```

## 🚀 Nächste Schritte

1. **Home Assistant Integration**: Verwende das neue modulare Design
2. **Android App**: Kommuniziere über die VoiceAssistant Klasse
3. **Web Interface**: REST API über Flask/FastAPI
4. **Datenbank**: Speichere Command-History
5. **Machine Learning**: Personalisierte Befehle

## 📄 Lizenz

Siehe Original-Repository: https://github.com/KoMMb0t/Computer-Voice-Assi

## 🤝 Beiträge

Willkommen! Bitte:
1. Neue Befehle über Command Pattern hinzufügen
2. Logging für Debugging verwenden
3. Type Hints verwenden
4. Docstrings schreiben

---

**Version:** 2.0 (Refactored)  
**Python:** 3.8+  
**Plattform:** Windows
