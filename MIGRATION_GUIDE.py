"""Migration Guide and Comparison: Old vs New Code

This document helps you understand the differences between the original
voice_assistant_edge_ultimate.py and the refactored version.
"""

# ============================================================================
# COMPARISON: OLD CODE vs NEW CODE
# ============================================================================

print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                    VOICE ASSISTANT: CODE COMPARISON                        ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

# ============================================================================
# 1. CONFIGURATION
# ============================================================================

print("\n1️⃣  CONFIGURATION MANAGEMENT")
print("="*80)

print("\n❌ OLD CODE:")
print("""
# Hard-coded "magic numbers" everywhere
WAKE_WORD = "hey jarvis"
SAMPLE_RATE = 16000
CHUNK_SAMPLES = 1280
SILENCE_TIMEOUT = 2.0
MAX_RECORD_TIME = 30
TTS_VOICE = "de-DE-KatjaNeural"

# Changes require code modification
if SAMPLE_RATE != 16000:
    # Recompile entire app
""")

print("\n✅ NEW CODE:")
print("""
# Centralized YAML configuration
from config import Config

config = Config()
sample_rate = config.get('audio.sample_rate')
voice = config.get('text_to_speech.voice')

# Changes are simple - just edit config.yaml
# No code recompilation needed!

# Access via properties
audio_cfg = config.audio
wake_word_cfg = config.wake_word
""")

# ============================================================================
# 2. COMPONENT INITIALIZATION
# ============================================================================

print("\n2️⃣  COMPONENT INITIALIZATION")
print("="*80)

print("\n❌ OLD CODE:")
print("""
# Global variable for pause state
wake_word_paused = False

# Initialization mixed in main()
def main():
    global wake_word_paused
    
    speak("Initialisiere System")
    
    print("Lade Wake-Word-Modell...")
    oww_model = Model(wakeword_models=["hey_jarvis"])
    
    print("Lade Speech-to-Text-Modell...")
    vosk_model = VoskModel(lang="de")
    
    # Hard to test, hard to reuse
""")

print("\n✅ NEW CODE:")
print("""
# Class-based, dependency injection
class VoiceAssistant:
    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config()
        
        # Each component is independent
        self.audio_processor = AudioProcessor(
            sample_rate=config.audio['sample_rate'],
            chunk_samples=config.audio['chunk_samples']
        )
        self.wake_word_detector = WakeWordDetector(
            model_name=config.wake_word['model_name'],
            threshold=config.wake_word['threshold']
        )
        # ... other components ...

# Easy to test with mock config
test_config = Config()
test_assistant = VoiceAssistant(config=test_config)
""")

# ============================================================================
# 3. STATE MANAGEMENT
# ============================================================================

print("\n3️⃣  STATE MANAGEMENT (DOUBLE DETECTION FIX)")
print("="*80)

print("\n❌ OLD CODE:")
print("""
# Global state variable prone to race conditions
wake_word_paused = False
callback.detected = False
callback.in_cooldown = False

# Unclear state transitions
def listen_for_wake_word():
    callback.detected = False
    callback.in_cooldown = False
    
    with sd.InputStream(..., callback=callback):
        while not callback.detected:
            time.sleep(0.1)
    
    time.sleep(4.0)  # Cooldown
    
    with sd.InputStream(...) as stream:
        for _ in range(15):
            stream.read(CHUNK_SAMPLES)
    
# Timing issues cause double detection!
""")

print("\n✅ NEW CODE:")
print("""
# Explicit state machine
class AssistantState(Enum):
    IDLE = auto()
    LISTENING_FOR_COMMAND = auto()
    PROCESSING_COMMAND = auto()
    SPEAKING = auto()
    COOLDOWN = auto()

# Valid transitions defined
valid_transitions = {
    AssistantState.IDLE: [AssistantState.LISTENING_FOR_COMMAND],
    AssistantState.LISTENING_FOR_COMMAND: [AssistantState.PROCESSING_COMMAND],
    # ...
}

# State machine ensures:
# - Only valid transitions occur
# - No race conditions
# - Double detection impossible!

state_machine = StateMachine()
state_machine.transition(AssistantState.LISTENING_FOR_COMMAND)

# Cooldown is managed explicitly
state_machine.transition(AssistantState.COOLDOWN)
time.sleep(cooldown_seconds)
state_machine.transition(AssistantState.IDLE)
""")

# ============================================================================
# 4. ERROR HANDLING
# ============================================================================

print("\n4️⃣  ERROR HANDLING")
print("="*80)

print("\n❌ OLD CODE:")
print("""
def speak(text):
    print(f"[SPEAK] {text}")
    communicate = edge_tts.Communicate(text, TTS_VOICE)
    temp_file = "temp_speech.mp3"
    await communicate.save(temp_file)
    
    # What if save fails? Exception crashes app
    # What if device disconnects? No handling
    # What if file locked? Silently ignored with pass

try:
    time.sleep(0.3)
    os.remove(temp_file)
except Exception as e:
    # Falls Löschen fehlschlägt, ignorieren
    pass
""")

print("\n✅ NEW CODE:")
print("""
async def speak_async(self, text: str, temp_file: str = "temp_speech.mp3") -> None:
    \"\"\"Speak text asynchronously.\"\"\"
    try:
        self._is_speaking = True
        logger.info(f"Speaking: {text}")
        
        communicate = self.edge_tts.Communicate(text, self.voice)
        await communicate.save(temp_file)
        
        # Proper error handling
        if not os.path.exists(temp_file):
            logger.error(f"TTS file not created: {temp_file}")
            return
        
        pygame.mixer.music.load(temp_file)
        pygame.mixer.music.play()
        
        while pygame.mixer.music.get_busy():
            await asyncio.sleep(0.1)
        
        pygame.mixer.music.unload()
        
        try:
            await asyncio.sleep(0.3)
            if os.path.exists(temp_file):
                os.remove(temp_file)
        except Exception as e:
            logger.warning(f"Failed to delete temp file: {e}")
            # Logged, but doesn't crash app
        
        self._is_speaking = False
        logger.debug("Speech finished")
    
    except Exception as e:
        logger.error(f"Error during text-to-speech: {e}")
        self._is_speaking = False
""")

# ============================================================================
# 5. LOGGING
# ============================================================================

print("\n5️⃣  LOGGING & DEBUGGING")
print("="*80)

print("\n❌ OLD CODE:")
print("""
print(f"[LISTEN] Warte auf Wake Word '{WAKE_WORD}'...")
print(f"[DEBUG] Wake Word Score: {prediction['hey_jarvis']:.2f}")
print(f"[ACTION] Verarbeite: '{command_text}'")
print("\\n[LISTEN] Warte auf Wake Word...")

# No log file
# Can't change log level
# Hard to filter for debugging
# Mixed with stdout
""")

print("\n✅ NEW CODE:")
print("""
import logging

logger = logging.getLogger(__name__)

logger.debug("Wake word detection paused")
logger.info(f"Wake word detected with confidence: {confidence:.2f}")
logger.info(f"Processing command: '{command_text}'")
logger.warning("No matching command found")
logger.error(f"Error during speech recognition: {e}")

# Features:
# - Structured logging to file + console
# - Configurable log levels (DEBUG, INFO, WARNING, ERROR)
# - Rotating file handler (10MB max, 5 backups)
# - Timestamps and module names
# - Different formatters for console vs file

# Configure in config.yaml:
# logging:
#   level: DEBUG
#   file: voice_assistant.log
#   format: '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
""")

# ============================================================================
# 6. COMMANDS
# ============================================================================

print("\n6️⃣  COMMAND HANDLING (Command Pattern)")
print("="*80)

print("\n❌ OLD CODE:")
print("""
def execute_command(command_text):
    command_lower = command_text.lower()
    
    if "danke" in command_lower or "dankeschön" in command_lower:
        speak("Gern geschehen!")
        return
    
    if "taschenrechner" in command_lower or "rechner" in command_lower:
        speak("Öffne den Taschenrechner")
        subprocess.Popen("calc.exe")
    
    elif "editor" in command_lower or "notepad" in command_lower:
        speak("Öffne Notepad")
        subprocess.Popen("notepad.exe")
    
    elif "firefox" in command_lower:
        speak("Öffne Firefox")
        try:
            subprocess.Popen("firefox.exe")
        except FileNotFoundError:
            speak("Firefox ist nicht installiert")
    
    # Adding new commands requires modifying this huge function
    # No validation, no consistency
    # Hard to test individual commands
    # Difficult to enable/disable commands
""")

print("\n✅ NEW CODE:")
print("""
# Base command class
class BaseCommand(ABC):
    def __init__(self, name: str, description: str, keywords: list):
        self.name = name
        self.description = description
        self.keywords = keywords
    
    @abstractmethod
    def matches(self, text: str) -> bool:
        pass
    
    @abstractmethod
    def execute(self) -> str:
        pass

# Concrete command
class CalcCommand(BaseCommand):
    def __init__(self):
        super().__init__(
            name="calculator",
            description="Open calculator",
            keywords=["taschenrechner", "rechner"]
        )
    
    def matches(self, text: str) -> bool:
        return any(kw in text.lower() for kw in self.keywords)
    
    def execute(self) -> str:
        subprocess.Popen("calc.exe")
        return "Öffne den Taschenrechner"

# Registry manages all commands
class CommandRegistry:
    def __init__(self):
        self.commands = [
            CalcCommand(),
            NotepadCommand(),
            FirefoxCommand(),
            # ... more commands ...
        ]
    
    def find_command(self, text: str) -> Optional[BaseCommand]:
        for cmd in self.commands:
            if cmd.matches(text):
                return cmd
        return None

# Usage
registry = CommandRegistry()
cmd = registry.find_command("Öffne Taschenrechner")
if cmd:
    response = cmd.execute()
    tts_engine.speak(response)

# Benefits:
# - Easy to add new commands (just create new class)
# - Consistent interface
# - Easy to test (each command is isolated)
# - Can enable/disable commands easily
# - No huge if/elif chain
""")

# ============================================================================
# 7. TYPE HINTS
# ============================================================================

print("\n7️⃣  TYPE HINTS")
print("="*80)

print("\n❌ OLD CODE:")
print("""
def listen_for_wake_word(oww_model):
    # What type is oww_model? OpenWakeWord.Model? No idea!
    # What does it return? A bool? A tuple? Unclear!
    
    def callback(indata, frames, time, status):
        # What are these parameters? No hints!
        pass
    
    # Without hints, IDE can't help with autocomplete

def record_command_with_vad(vosk_model):
    # Returns audio_buffer, but what type?
    # bytes? List[bytes]? np.ndarray? Unknown!
    
    audio_buffer = []
    audio_buffer.append(bytes(audio_frame))
    
    return b''.join(audio_buffer)
    # Type checker can't verify correctness
""")

print("\n✅ NEW CODE:")
print("""
# Full type hints
def detect(self, audio_data: np.ndarray) -> Tuple[bool, float]:
    \"\"\"Detect wake word in audio data.
    
    Args:
        audio_data: Audio frame as numpy array
        
    Returns:
        Tuple of (detected: bool, confidence: float)
    \"\"\"
    pass

def recognize(self, audio_data: bytes, recognizer: 'KaldiRecognizer') -> str:
    \"\"\"Recognize speech from audio data.
    
    Args:
        audio_data: Audio data as bytes
        recognizer: KaldiRecognizer instance
        
    Returns:
        Recognized text or empty string if no match
    \"\"\"
    pass

# Benefits:
# - IDE autocomplete works
# - Type checkers (mypy) catch errors
# - Self-documenting code
# - Easier refactoring
# - Better tooling support
""")

# ============================================================================
# 8. TESTING & MODULARITY
# ============================================================================

print("\n8️⃣  TESTING & MODULARITY")
print("="*80)

print("\n❌ OLD CODE:")
print("""
# How do you test speak() in isolation?
# It depends on pygame.mixer (global state)
# It depends on edge_tts (network)
# No way to mock components!

# How do you test execute_command()?
# It has 20 different execution paths
# Each one depends on subprocess, webbrowser, etc.
# Very difficult to unit test
""")

print("\n✅ NEW CODE:")
print("""
# Components are independent and injectable
class TextToSpeechEngine:
    def __init__(self, voice: str = "de-DE-KatjaNeural"):
        self.voice = voice
        # Can be mocked in tests!

def test_speak():
    mock_tts = MagicMock(spec=TextToSpeechEngine)
    mock_tts.speak.return_value = None
    
    # Test with mock
    mock_tts.speak("Hello")
    mock_tts.speak.assert_called_with("Hello")

# Commands are easy to test
class TestCalcCommand:
    def test_matches(self):
        cmd = CalcCommand()
        assert cmd.matches("Taschenrechner")
        assert cmd.matches("Rechner")
        assert not cmd.matches("Notepad")
    
    def test_execute(self):
        cmd = CalcCommand()
        response = cmd.execute()
        assert response == "Öffne den Taschenrechner"

# With separate components:
# - Each component can be tested in isolation
# - Mocking is easy
# - Dependencies are explicit
# - Integration tests are cleaner
""")

# ============================================================================
# MIGRATION CHECKLIST
# ============================================================================

print("\n" + "="*80)
print("MIGRATION CHECKLIST")
print("="*80)

checklist = [
    ("Install dependencies", "pip install -r requirements.txt"),
    ("Download Vosk model", "python download_models.py"),
    ("Copy config.yaml", "Place in project root"),
    ("Test individual components", "Test audio, wake word, STT, TTS"),
    ("Test state transitions", "Monitor logs for state changes"),
    ("Test commands", "Try each command manually"),
    ("Adjust config.yaml", "Tune threshold, cooldown if needed"),
    ("Monitor logs", "Check voice_assistant.log for issues"),
]

for i, (task, cmd) in enumerate(checklist, 1):
    status = "□"
    print(f"{status} {i}. {task:<40} → {cmd}")

# ============================================================================
# SUMMARY
# ============================================================================

print("\n" + "="*80)
print("SUMMARY OF IMPROVEMENTS")
print("="*80)

improvements = {
    "Code Quality": [
        "❌ Global variables      → ✅ OOP + Dependency Injection",
        "❌ No type hints        → ✅ Full type annotations",
        "❌ Minimal docs         → ✅ Google-style docstrings",
        "❌ print() statements   → ✅ Structured logging",
    ],
    "Robustness": [
        "❌ Race conditions      → ✅ State machine validation",
        "❌ Double detection     → ✅ Explicit cooldown states",
        "❌ Error silence        → ✅ Try/except + logging",
        "❌ Hard-coded values    → ✅ YAML configuration",
    ],
    "Maintainability": [
        "❌ Huge if/elif chains  → ✅ Command pattern",
        "❌ Global functions     → ✅ Component classes",
        "❌ No separation        → ✅ Single responsibility",
        "❌ Difficult to extend  → ✅ Plugin-like architecture",
    ],
}

for category, items in improvements.items():
    print(f"\n{category}:")
    for item in items:
        print(f"  {item}")

print("\n" + "="*80)
print("Ready to upgrade? Start with: python main.py")
print("="*80)
