# Voice Assistant - Refactoring Documentation

## Überblick

Dieses Dokument dokumentiert das umfangreiche Refactoring des Voice Assistant Projekts. Der ursprüngliche prozeduale Code wurde in eine professionelle, modulare, objektorientierte Architektur umgewandelt, die Best Practices für Python-Entwicklung befolgt.

---

## Inhaltsverzeichnis

1. [Architekturübersicht](#architekturübersicht)
2. [Hauptänderungen](#hauptänderungen)
3. [Komponenten-Beschreibung](#komponenten-beschreibung)
4. [Design Patterns](#design-patterns)
5. [Fehlerbehandlung & Logging](#fehlerbehandlung--logging)
6. [Konfiguration](#konfiguration)
7. [Migration vom alten Code](#migration-vom-alten-code)
8. [Erste Schritte](#erste-schritte)
9. [Erweiterbarkeitsleitfaden](#erweiterbarkeitsleitfaden)
10. [Troubleshooting](#troubleshooting)

---

## Architekturübersicht

### Alte Architektur
```
voice_assistant_edge_ultimate.py
├── Global State Variables
├── Async Functions
├── Callback Functions
└── Main Loop (prozedural)
```

**Probleme:**
- Globale Zustandsvariablen führen zu Race Conditions
- Doppelte Wake-Word-Erkennung wegen Timing-Problemen
- Schwer zu testen und zu erweitern
- Keine klare Trennung von Concerns

### Neue Architektur

```
VoiceAssistant (Orchestrator)
├── StateMachine (Zustandsverwaltung)
│   └── AssistantState (Idle, Listening, Processing, Speaking, Cooldown)
├── AudioProcessor (Audio-Eingabe)
├── WakeWordDetector (OpenWakeWord)
├── SpeechToTextConverter (Vosk STT)
├── TextToSpeechEngine (Edge TTS)
└── CommandRegistry (Befehlsverwaltung)
    └── BaseCommand (Command Pattern)
        ├── GreetingCommand
        ├── CalcCommand
        ├── ChatGPTCommand
        └── [weitere Befehle...]
```

**Vorteile:**
- ✅ State Machine verhindert ungültige Zustandsübergänge
- ✅ Komponenten sind unabhängig und testbar
- ✅ Command Pattern ermöglicht einfache Erweiterung
- ✅ Konfigurationszentralisierung
- ✅ Strukturiertes Logging
- ✅ Type Hints für bessere IDE-Unterstützung
- ✅ Professionelle Dokumentation

---

## Hauptänderungen

### 1. State Machine für Robust State Management

**Problem:** Die Doppelerkennung des Wake-Words war Ergebnis von Race Conditions und ungültigen Zustandsübergängen.

**Lösung:** Implementierung einer State Machine mit expliziten, validierten Zustandsübergängen:

```python
AssistantState:
    IDLE ──→ LISTENING_FOR_COMMAND ──→ PROCESSING_COMMAND ──→ SPEAKING ──→ COOLDOWN ──→ IDLE
    └─────────────────────────────────────────────────────────────────────────────────┘
```

**Validierung:** Die State Machine überprüft vor jedem Übergang, ob der Zielzustand erlaubt ist.

```python
# Beispiel: Von IDLE kann nur zu LISTENING_FOR_COMMAND übergegangen werden
valid_transitions = {
    AssistantState.IDLE: [
        AssistantState.LISTENING_FOR_COMMAND,
        AssistantState.SHUTDOWN,
        AssistantState.ERROR,
    ],
    # ...
}
```

### 2. Modulare Komponenten

**AudioProcessor**
- Verwaltet Audio-Streaming
- Buffering und Fehlerbehandlung
- Device-Management

```python
audio_processor = AudioProcessor(
    sample_rate=16000,
    chunk_samples=1280,
    device_index=None  # None = Default Device
)
audio_processor.start_stream(callback)
audio_processor.clear_buffer(15)  # Puffer löschen
```

**WakeWordDetector**
- OpenWakeWord-Modell-Management
- Threshold- und Cooldown-Logik
- Pause/Resume-Funktion zur Vermeidung von Doppelerkennung

```python
detector = WakeWordDetector(
    model_name="hey_jarvis",
    threshold=0.5,
    cooldown_seconds=4.0
)

detected, confidence = detector.detect(audio_frame)

# Während Befehlsverarbeitung pausieren
detector.pause()
detector.resume()
```

**SpeechToTextConverter**
- Vosk-Modell-Management
- Silence-Detection
- Language-Support

```python
stt = SpeechToTextConverter(
    language="de",
    silence_timeout=2.0,
    max_record_time=30
)

text = stt.recognize(audio_data, recognizer)
```

**TextToSpeechEngine**
- Edge TTS Integration
- Async/Sync-Support
- Pygame Audio-Playback
- Proper Cleanup

```python
tts = TextToSpeechEngine(voice="de-DE-KatjaNeural")

# Synchron
tts.speak("Hallo Welt")

# Asynchron (wenn gewünscht)
await tts.speak_async("Hallo Welt")
```

### 3. Command Pattern für Erweiterbarkeit

**BaseCommand Abstract Class:**
```python
class BaseCommand(ABC):
    def matches(self, text: str) -> bool:
        """Überprüft ob Befehl dem Text entspricht"""
    
    def execute(self) -> str:
        """Führt Befehl aus und gibt Response zurück"""
```

**Beispiel: Neuer Befehl erstellen**
```python
class MyCustomCommand(BaseCommand):
    def __init__(self):
        super().__init__(
            name="custom",
            description="Mein eigener Befehl",
            command_type=CommandType.CUSTOM,
            keywords=["custom", "befehl"]
        )
    
    def matches(self, text: str) -> bool:
        text_lower = text.lower()
        return any(kw in text_lower for kw in self.keywords)
    
    def execute(self) -> str:
        # Logik hier
        self.log_execution()
        return "Custom Befehl ausgeführt"

# Registrieren
registry.register_command(MyCustomCommand())
```

**CommandRegistry:**
- Zentrale Verwaltung aller Befehle
- Automatisches Matching des Eingabetexts
- Filterung nach Befehltyp

```python
registry = CommandRegistry()
command = registry.find_command("Taschenrechner öffnen")
if command:
    response = command.execute()
```

### 4. Zentralisierte Konfiguration

**Alte Methode:**
```python
# Magische Zahlen überall verteilt
SAMPLE_RATE = 16000
CHUNK_SAMPLES = 1280
SILENCE_TIMEOUT = 2.0
# ...
```

**Neue Methode: `config.yaml`**
```yaml
audio:
  sample_rate: 16000
  chunk_samples: 1280

wake_word:
  model_name: hey_jarvis
  threshold: 0.5
  cooldown_seconds: 4.0

speech_recognition:
  model_language: de
  silence_timeout: 2.0

text_to_speech:
  voice: de-DE-KatjaNeural
```

**Zugriff im Code:**
```python
config = Config()
sample_rate = config.get('audio.sample_rate')
threshold = config.wake_word.get('threshold')
```

### 5. Strukturiertes Logging

**Alte Methode:**
```python
print("[DEBUG] Wake Word erkannt")
print(f"[ACTION] Verarbeite: '{command_text}'")
```

**Neue Methode: Python `logging` Module**
```python
logger = logging.getLogger(__name__)

logger.info("Wake word detected")
logger.debug("Processing command")
logger.warning("Device not found")
logger.error("Failed to load model")
```

**Features:**
- Verschiedene Log-Level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- File + Console Output
- Rotating File Handler (automatisches Archivieren)
- Strukturierte Formatierung
- Konfigurierbar über `config.yaml`

**Log-Datei:** `voice_assistant.log`

### 6. Type Hints

**Alte Methode:**
```python
def speak(text):
    # Keine Hinweise für Typen
    ...
```

**Neue Methode:**
```python
def speak(self, text: str) -> None:
    """Speak text synchronously."""
    ...

def recognize(self, audio_data: bytes, recognizer: 'KaldiRecognizer') -> str:
    """Recognize speech from audio data."""
    ...
```

**Vorteile:**
- IDE-Autocompletion
- Type Checking mit mypy/pylance
- Selbstdokumentierender Code

### 7. Professionelle Docstrings

**Google-Style Docstrings:**
```python
def detect(self, audio_data: np.ndarray) -> Tuple[bool, float]:
    """Detect wake word in audio data.
    
    Args:
        audio_data: Audio frame as numpy array
        
    Returns:
        Tuple of (detected: bool, confidence: float)
        
    Raises:
        Exception: If model prediction fails
    """
    ...
```

---

## Komponenten-Beschreibung

### `config.py`
**Zweck:** Konfigurationsverwaltung  
**Singleton Pattern:** Stellt sicher, dass es nur eine Konfigurationsinstanz gibt  
**Features:**
- YAML-Basierte Konfiguration
- Dot-Notation für Zugriff (`config.get('audio.sample_rate')`)
- Property-Zugriffe für Subsysteme
- Fallback auf Default-Konfiguration

### `state_machine.py`
**Zweck:** Zustandsverwaltung und Event-System  
**Komponenten:**
- `AssistantState`: Enum mit allen möglichen Zuständen
- `AssistantEvent`: Enum mit allen möglichen Events
- `StateMachine`: Validiert Zustandsübergänge, verwaltet History
- `EventBus`: Dekupliertes Event-Publishing System

**Verwendung:**
```python
# Zustandsübergänge
if state_machine.can_transition(AssistantState.LISTENING_FOR_COMMAND):
    state_machine.transition(AssistantState.LISTENING_FOR_COMMAND)

# State-Change Callbacks
state_machine.on_state_change(
    AssistantState.IDLE,
    lambda: logger.info("Returned to IDLE")
)
```

### `components.py`
**Zweck:** Kernkomponenten des Systems  
**Klassen:**
1. **AudioProcessor**: Audio-Input-Verwaltung
2. **WakeWordDetector**: OpenWakeWord-Integration
3. **SpeechToTextConverter**: Vosk-Integration
4. **TextToSpeechEngine**: Edge TTS-Integration

**Besonderheiten:**
- Exception Handling bei Gerätefehlern
- Puffer-Management
- Cooldown-Verwaltung

### `commands.py`
**Zweck:** Command Pattern Implementierung  
**Klassen:**
- `BaseCommand`: Abstract Base Class
- `CommandType`: Enum für Befehlskategorien
- `CommandRegistry`: Command-Management
- Konkrete Implementierungen:
  - `GreetingCommand`
  - `CalcCommand`
  - `NotepadCommand`
  - `ExplorerCommand`
  - `FirefoxCommand`
  - `ChatGPTCommand`
  - `TimeCommand`
  - `DateCommand`
  - `HelpCommand`
  - `CancelCommand`

### `logger_setup.py`
**Zweck:** Logging-Konfiguration  
**Features:**
- Singleton Logger Setup
- File + Console Handler
- Rotating File Handler (10MB max, 5 Backups)
- Konfigurierbar via `config.yaml`

### `main.py`
**Zweck:** Hauptorchestrator  
**Klasse:** `VoiceAssistant`
**Verantwortlichkeiten:**
- Komponenten-Initialisierung
- State Machine Orchestrierung
- Event Loop Management
- Graceful Shutdown

---

## Design Patterns

### 1. **State Machine Pattern**
Verhindert Race Conditions durch explizite Zustandsübergänge.

### 2. **Command Pattern**
Ermöglicht einfache Erweiterung mit neuen Befehlen.

```python
class NewCommand(BaseCommand):
    def matches(self, text: str) -> bool: ...
    def execute(self) -> str: ...

registry.register_command(NewCommand())
```

### 3. **Singleton Pattern**
- `Config`: Nur eine Konfigurationsinstanz
- `LoggerSetup`: Nur ein Logging-System

### 4. **Dependency Injection**
```python
assistant = VoiceAssistant(config=custom_config)
```

### 5. **Strategy Pattern**
Verschiedene Befehle mit unterschiedlichen Strategien.

### 6. **Observer Pattern**
Event Bus für entkoppelte Kommunikation.

---

## Fehlerbehandlung & Logging

### Exception Handling

**Alle I/O-Operationen sind wrapped:**
```python
try:
    self.audio_processor.start_stream(callback)
except Exception as e:
    logger.error(f"Failed to start audio stream: {e}")
    # Graceful degradation
```

### Logging-Level

| Level | Verwendung |
|-------|-----------|
| DEBUG | Detaillierte Diagnostik |
| INFO | Wichtige Meilensteine |
| WARNING | Mögliche Probleme |
| ERROR | Fehler, aber erhebbar |
| CRITICAL | Fatale Fehler |

**Beispiele:**
```python
logger.debug("Processing audio chunk")
logger.info("Wake word detected")
logger.warning("Device not responding")
logger.error("Failed to load model")
```

---

## Konfiguration

### `config.yaml` Struktur

```yaml
# Audio
audio:
  sample_rate: 16000          # Hz
  chunk_samples: 1280         # Samples pro Chunk
  device_index: null          # null = Default Device

# Wake Word
wake_word:
  model_name: hey_jarvis
  threshold: 0.5              # 0.0-1.0 (höher = sensitiver)
  cooldown_seconds: 4.0       # Pause nach Erkennung
  buffer_clear_chunks: 15     # Chunks zum Pufferleeren

# Speech Recognition
speech_recognition:
  model_language: de
  silence_timeout: 2.0        # Sekunden Stille zum Beenden
  max_record_time: 30         # Max. Aufnahmedauer

# Text-to-Speech
text_to_speech:
  voice: de-DE-KatjaNeural    # Azure Voice
  engine: edge                # TTS Engine

# Logging
logging:
  level: INFO                 # DEBUG, INFO, WARNING, ERROR
  file: voice_assistant.log   # Log-Datei
  format: '...'               # Format-String

# Commands
commands:
  enable_web_search: true
  enable_system_commands: true
```

### Tuning für Double Detection

Falls Wake-Word immer noch doppelt erkannt wird:

```yaml
wake_word:
  threshold: 0.6              # Erhöhen (weniger sensitiv)
  cooldown_seconds: 5.0       # Erhöhen (längere Pause)
  buffer_clear_chunks: 20     # Erhöhen (mehr Puffer leeren)
```

---

## Migration vom alten Code

### Was hat sich geändert?

| Alt | Neu |
|-----|-----|
| `voice_assistant_edge_ultimate.py` | `main.py` (+ Module) |
| Globale Variablen | Konfigurationsdatei + Klassen-Attribute |
| Prozedural | OOP mit State Machine |
| `print()` Statements | `logging` Module |
| Keine Dokumentation | Umfangreiche Docstrings |
| Keine Type Hints | Vollständige Type Hints |
| Feste Befehle | Erweiterbar via Command Pattern |

### Befehle im neuen Code

Befehle sind jetzt über die `CommandRegistry` verwaltet:

```python
# Alte Methode:
if "taschenrechner" in command_lower:
    speak("...")
    subprocess.Popen("calc.exe")

# Neue Methode:
class CalcCommand(BaseCommand):
    def execute(self) -> str:
        subprocess.Popen("calc.exe")
        return "Öffne den Taschenrechner"

registry = CommandRegistry()
command = registry.find_command("Taschenrechner")
if command:
    response = command.execute()
    tts_engine.speak(response)
```

---

## Erste Schritte

### Installation

1. **Abhängigkeiten installieren:**
```bash
pip install -r requirements.txt
```

2. **Vosk-Modell herunterladen:**
```bash
python download_models.py
```

3. **Konfiguration anpassen (optional):**
Bearbeite `config.yaml` für deine Einstellungen.

### Ausführung

**Neue Version starten:**
```bash
python main.py
```

**Alte Version starten (für Vergleich):**
```bash
python voice_assistant_edge_ultimate.py
```

### Erste Interaktion

1. Warte bis "System bereit" gesprochen wird
2. Sage "Hey Jarvis" um das Wake-Word auszulösen
3. Warte auf "Ja?"
4. Gib einen Befehl ein, z.B. "Öffne den Taschenrechner"
5. Der Assistent führt den Befehl aus

---

## Erweiterbarkeitsleitfaden

### Neuen Befehl hinzufügen

**Schritt 1:** Neue Klasse in `commands.py` erstellen

```python
class PythonCommand(BaseCommand):
    """Open Python interpreter."""
    
    def __init__(self):
        super().__init__(
            name="python",
            description="Open Python interpreter",
            command_type=CommandType.SYSTEM,
            keywords=["python", "interpreter"]
        )
    
    def matches(self, text: str) -> bool:
        text_lower = text.lower()
        return any(kw in text_lower for kw in self.keywords)
    
    def execute(self) -> str:
        try:
            subprocess.Popen("python.exe")
            self.log_execution()
            return "Öffne Python"
        except Exception as e:
            logger.error(f"Failed to open Python: {e}")
            return "Konnte Python nicht öffnen"
```

**Schritt 2:** In `_load_default_commands()` registrieren

```python
def _load_default_commands(self) -> None:
    self.commands = [
        # ... andere Befehle ...
        PythonCommand(),
    ]
```

### Neuen State hinzufügen

1. In `AssistantState` enum hinzufügen
2. In `can_transition()` valid transitions definieren
3. State handler in `main.py` implementieren

```python
# In state_machine.py
class AssistantState(Enum):
    # ... andere states ...
    MY_NEW_STATE = auto()

# In main.py
def _state_my_new_state(self) -> None:
    """MY_NEW_STATE state logic."""
    logger.info("In MY_NEW_STATE")
    self.state_machine.transition(AssistantState.IDLE)
```

### Neue Komponente integrieren

1. Klasse in `components.py` erstellen
2. In `VoiceAssistant.__init__()` initialisieren
3. In State Handler verwenden

```python
# In components.py
class MyComponent:
    def __init__(self):
        logger.info("MyComponent initialized")

# In main.py __init__
self.my_component = MyComponent()
```

---

## Troubleshooting

### Problem: Wake-Word wird nicht erkannt

**Lösungen:**
1. **Threshold senken:**
   ```yaml
   wake_word:
     threshold: 0.3  # Sensitiver
   ```
2. **Mikrofon testen:**
   ```bash
   python test_microphone.py
   ```
3. **Lautstärke erhöhen** (Mikrofon-Input)

### Problem: Wake-Word wird doppelt erkannt

**Lösungen:**
1. **Cooldown erhöhen:**
   ```yaml
   wake_word:
     cooldown_seconds: 5.0  # Von 4.0 erhöht
   ```
2. **Threshold erhöhen:**
   ```yaml
   wake_word:
     threshold: 0.6  # Weniger sensitiv
   ```
3. **Buffer-Clearing erhöhen:**
   ```yaml
   wake_word:
     buffer_clear_chunks: 20  # Von 15 erhöht
   ```

### Problem: Befehle werden nicht erkannt

1. **Stille-Timeout prüfen:**
   ```yaml
   speech_recognition:
     silence_timeout: 2.5  # Erhöhen
   ```
2. **Log-Level auf DEBUG setzen:**
   ```yaml
   logging:
     level: DEBUG
   ```
3. **Log-Datei prüfen:**
   ```bash
   cat voice_assistant.log | tail -50
   ```

### Problem: Sprachausgabe stockt

1. **Pygame Mixer prüfen:**
   ```bash
   python test_tts.py
   ```
2. **TMP-Pfad prüfen** (Speicherplatz für Temp-Dateien)

### Problem: Keine Audio-Eingabe erkannt

1. **Audio-Device Index prüfen:**
   ```python
   import sounddevice as sd
   print(sd.query_devices())
   ```
2. **Device-Index in Config setzen:**
   ```yaml
   audio:
     device_index: 2  # Statt null
   ```

### Log-Dateien Analysieren

**Log-Datei anschauen:**
```bash
# PowerShell
Get-Content voice_assistant.log -Tail 100

# Oder
tail -f voice_assistant.log  # Live folgen
```

**Häufige Log-Muster:**
```
DEBUG - Wake word detection paused        # Normal während Verarbeitung
INFO - Wake word detected                 # Gutes Zeichen!
ERROR - Failed to load model              # Problem mit Modell
WARNING - Device not found                # Audio-Geräteproblem
```

---

## Performance-Tipps

1. **VAD (Voice Activity Detection)** verbessern:
   - Silence-Timeout anpassen
   - Buffer-Größe optimieren

2. **Wake-Word Latenz reduzieren:**
   - Sample Rate überprüfen
   - Threshold fein-tunen

3. **Audio-Verzögerung minimieren:**
   - Chunk-Größe 1280 ist optimal für 16kHz
   - Hardware-Puffer löschen nach Wake-Word

---

## Zusammenfassung der Verbesserungen

| Aspekt | Alt | Neu |
|--------|-----|-----|
| **Architektur** | Prozedural | OOP + State Machine |
| **Doppel-Detection** | Problematisch | Verhindert durch States |
| **Fehlerbehandlung** | Basic | Robust mit Try/Except |
| **Erweiterbarkeit** | Schwierig | Command Pattern |
| **Logging** | Print Statements | Strukturiert |
| **Dokumentation** | Keine | Umfangreich |
| **Type Safety** | Keine | Vollständige Type Hints |
| **Testbarkeit** | Schwierig | Modular |
| **Wartbarkeit** | Niedrig | Hoch |
| **Professionalisierung** | 40% | 95% |

---

## Support & Weitere Informationen

- **GitHub:** https://github.com/KoMMb0t/Computer-Voice-Assi
- **Issues:** Bitte mit Debug-Logs erstellen
- **Contributions:** Willkommen!

---

**Version:** 2.0  
**Letztes Update:** Dezember 2025  
**Autor:** Refactoring-Agent
