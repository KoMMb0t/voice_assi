"""Main Voice Assistant orchestrator.

The VoiceAssistant class coordinates all components and manages the overall
flow of the application using a state machine to prevent race conditions.
"""

import logging
import time
import threading
from typing import Optional
import numpy as np

from config import Config
from logger_setup import LoggerSetup
from state_machine import StateMachine, AssistantState, AssistantEvent, Event
from components import (
    AudioProcessor,
    WakeWordDetector,
    SpeechToTextConverter,
    TextToSpeechEngine
)
from commands import CommandRegistry

logger = logging.getLogger(__name__)


class VoiceAssistant:
    """Main Voice Assistant class.
    
    Orchestrates all components and manages the interaction flow using
    a state machine to prevent race conditions and double detection.
    
    Attributes:
        state_machine: State machine managing assistant states
        audio_processor: Handles audio input
        wake_word_detector: Detects wake words
        stt_converter: Converts speech to text
        tts_engine: Synthesizes text to speech
        command_registry: Manages available commands
    """
    
    def __init__(self, config: Optional[Config] = None):
        """Initialize Voice Assistant.
        
        Args:
            config: Configuration object (uses singleton if not provided)
        """
        self.config = config or Config()
        
        # Initialize logging
        LoggerSetup.setup()
        logger.info("="*60)
        logger.info("Voice Assistant Initializing")
        logger.info("="*60)
        
        # Initialize components
        self.state_machine = StateMachine()
        self._setup_state_callbacks()
        
        try:
            # Audio component
            audio_cfg = self.config.audio
            self.audio_processor = AudioProcessor(
                sample_rate=audio_cfg.get('sample_rate', 16000),
                chunk_samples=audio_cfg.get('chunk_samples', 1280),
                device_index=audio_cfg.get('device_index'),
            )
            logger.info("✓ Audio processor initialized")
            
            # Wake word detector
            ww_cfg = self.config.wake_word
            self.wake_word_detector = WakeWordDetector(
                model_name=ww_cfg.get('model_name', 'hey_jarvis'),
                threshold=ww_cfg.get('threshold', 0.5),
                cooldown_seconds=ww_cfg.get('cooldown_seconds', 4.0),
            )
            logger.info("✓ Wake word detector initialized")
            
            # Speech-to-text converter
            stt_cfg = self.config.speech_recognition
            self.stt_converter = SpeechToTextConverter(
                language=stt_cfg.get('model_language', 'de'),
                silence_timeout=stt_cfg.get('silence_timeout', 2.0),
                max_record_time=stt_cfg.get('max_record_time', 30),
            )
            logger.info("✓ Speech-to-text converter initialized")
            
            # Text-to-speech engine
            tts_cfg = self.config.text_to_speech
            self.tts_engine = TextToSpeechEngine(
                voice=tts_cfg.get('voice', 'de-DE-KatjaNeural')
            )
            logger.info("✓ Text-to-speech engine initialized")
            
            # Command registry
            self.command_registry = CommandRegistry()
            logger.info("✓ Command registry initialized")
            
            logger.info("="*60)
            logger.info("✓ Voice Assistant Ready")
            logger.info("="*60)
        
        except Exception as e:
            logger.error(f"Failed to initialize Voice Assistant: {e}")
            raise
    
    def _setup_state_callbacks(self) -> None:
        """Setup callbacks for state transitions."""
        self.state_machine.on_state_change(
            AssistantState.IDLE,
            lambda: logger.debug("State: IDLE - Listening for wake word")
        )
        self.state_machine.on_state_change(
            AssistantState.LISTENING_FOR_COMMAND,
            lambda: logger.debug("State: LISTENING_FOR_COMMAND - Recording user input")
        )
        self.state_machine.on_state_change(
            AssistantState.PROCESSING_COMMAND,
            lambda: logger.debug("State: PROCESSING_COMMAND - Executing command")
        )
        self.state_machine.on_state_change(
            AssistantState.SPEAKING,
            lambda: logger.debug("State: SPEAKING - Playing TTS response")
        )
        self.state_machine.on_state_change(
            AssistantState.COOLDOWN,
            lambda: logger.debug("State: COOLDOWN - In cooldown period")
        )
    
    def start(self) -> None:
        """Start the voice assistant main loop."""
        logger.info("Starting Voice Assistant main loop")
        
        try:
            # Initial greeting
            self.tts_engine.speak("System bereit")
            
            # Main event loop
            while self.state_machine.current_state != AssistantState.SHUTDOWN:
                self._process_state()
                time.sleep(0.05)  # Small sleep to prevent busy-waiting
        
        except KeyboardInterrupt:
            logger.info("Shutdown requested by user (Ctrl+C)")
            self.shutdown()
        except Exception as e:
            logger.error(f"Error in main loop: {e}")
            self.shutdown()
    
    def _process_state(self) -> None:
        """Process the current state."""
        current_state = self.state_machine.current_state
        
        if current_state == AssistantState.IDLE:
            self._state_idle()
        elif current_state == AssistantState.LISTENING_FOR_COMMAND:
            self._state_listening()
        elif current_state == AssistantState.PROCESSING_COMMAND:
            self._state_processing()
        elif current_state == AssistantState.SPEAKING:
            self._state_speaking()
        elif current_state == AssistantState.COOLDOWN:
            self._state_cooldown()
    
    def _state_idle(self) -> None:
        """IDLE state: Listen for wake word."""
        if self.wake_word_detector._is_paused:
            self.wake_word_detector.resume()
        
        # Setup audio callback for wake word detection
        wake_detected = False
        
        def audio_callback(indata, frames, time_info, status):
            nonlocal wake_detected
            if status:
                logger.debug(f"Audio status: {status}")
            
            audio_frame = np.frombuffer(indata, dtype=np.int16)
            detected, confidence = self.wake_word_detector.detect(audio_frame)
            
            if detected:
                logger.info(f"Wake word detected (confidence: {confidence:.2f})")
                wake_detected = True
        
        # Start listening with short timeout
        if self.audio_processor.start_stream(audio_callback):
            # Listen for a short period
            start_time = time.time()
            while not wake_detected and (time.time() - start_time) < 0.5:
                time.sleep(0.05)
            
            self.audio_processor.stop_stream()
            
            if wake_detected:
                logger.info("Transition: IDLE -> LISTENING_FOR_COMMAND")
                self.state_machine.transition(AssistantState.LISTENING_FOR_COMMAND)
    
    def _state_listening(self) -> None:
        """LISTENING_FOR_COMMAND state: Record and recognize speech."""
        logger.info("Recording command...")
        
        # Pause wake word detection
        self.wake_word_detector.pause()
        
        # Clear audio buffer
        buffer_clear_chunks = self.config.wake_word.get('buffer_clear_chunks', 15)
        self.audio_processor.clear_buffer(buffer_clear_chunks)
        
        # Speak confirmation
        self.tts_engine.speak("Ja?")
        time.sleep(0.5)
        
        # Record and recognize command
        command_text = self._record_and_recognize()
        
        if command_text:
            logger.info(f"Recognized: '{command_text}'")
            self.state_machine.transition(AssistantState.PROCESSING_COMMAND)
            # Store recognized command for processing
            self._pending_command = command_text
        else:
            logger.warning("No command recognized")
            self.state_machine.transition(AssistantState.COOLDOWN)
            self._pending_command = None
    
    def _record_and_recognize(self) -> str:
        """Record audio and convert to text.
        
        Returns:
            Recognized text or empty string if no match
        """
        import json
        
        try:
            recognizer = self.stt_converter.create_recognizer()
            audio_buffer = []
            last_speech_time = time.time()
            recording_started = False
            start_time = time.time()
            
            def audio_callback(indata, frames, time_info, status):
                nonlocal last_speech_time, recording_started
                
                audio_frame = np.frombuffer(indata, dtype=np.int16)
                audio_buffer.append(bytes(audio_frame))
                
                if recognizer.AcceptWaveform(bytes(audio_frame)):
                    result = json.loads(recognizer.Result())
                    if result.get("text", ""):
                        last_speech_time = time.time()
                        recording_started = True
            
            # Start recording
            if self.audio_processor.start_stream(audio_callback):
                silence_timeout = self.config.speech_recognition.get('silence_timeout', 2.0)
                max_record_time = self.config.speech_recognition.get('max_record_time', 30)
                
                while True:
                    current_time = time.time()
                    
                    # Check if silence timeout reached
                    if recording_started and (current_time - last_speech_time) > silence_timeout:
                        logger.info("Silence detected - ending recording")
                        break
                    
                    # Check if max recording time reached
                    if (current_time - start_time) > max_record_time:
                        logger.info("Max recording time reached")
                        break
                    
                    time.sleep(0.05)
                
                self.audio_processor.stop_stream()
                
                # Get final result
                if audio_buffer:
                    audio_data = b''.join(audio_buffer)
                    return self.stt_converter.recognize(audio_data, recognizer)
        
        except Exception as e:
            logger.error(f"Error during recording: {e}")
        
        return ""
    
    def _state_processing(self) -> None:
        """PROCESSING_COMMAND state: Execute the recognized command."""
        command_text = getattr(self, '_pending_command', None)
        
        if not command_text:
            self.state_machine.transition(AssistantState.IDLE)
            return
        
        logger.info(f"Processing command: '{command_text}'")
        
        # Find and execute command
        command = self.command_registry.find_command(command_text)
        
        if command:
            try:
                response = command.execute()
                logger.info(f"Command executed: {command.name}")
                
                # Transition to speaking
                self._pending_response = response
                self.state_machine.transition(AssistantState.SPEAKING)
            except Exception as e:
                logger.error(f"Error executing command {command.name}: {e}")
                self._pending_response = "Fehler bei der Ausführung"
                self.state_machine.transition(AssistantState.SPEAKING)
        else:
            logger.warning("No matching command found")
            self._pending_response = "Befehl nicht erkannt"
            self.state_machine.transition(AssistantState.SPEAKING)
    
    def _state_speaking(self) -> None:
        """SPEAKING state: Play TTS response."""
        response = getattr(self, '_pending_response', "")
        
        if response:
            logger.info(f"Speaking: {response}")
            self.tts_engine.speak(response)
        
        # Transition to cooldown
        self.state_machine.transition(AssistantState.COOLDOWN)
    
    def _state_cooldown(self) -> None:
        """COOLDOWN state: Wait before listening for wake word again."""
        cooldown_time = self.config.wake_word.get('cooldown_seconds', 4.0)
        logger.info(f"Entering cooldown for {cooldown_time} seconds")
        
        time.sleep(cooldown_time)
        
        # Resume wake word detection and return to IDLE
        self.wake_word_detector.resume()
        self.state_machine.transition(AssistantState.IDLE)
    
    def shutdown(self) -> None:
        """Shutdown the voice assistant."""
        logger.info("Shutting down Voice Assistant")
        
        try:
            # Speak goodbye
            self.tts_engine.speak("Auf Wiedersehen")
            
            # Stop audio processor
            self.audio_processor.stop_stream()
            
            # Cleanup TTS
            self.tts_engine.cleanup()
            
            # Transition to shutdown state
            self.state_machine.transition(AssistantState.SHUTDOWN)
            
            logger.info("Voice Assistant shutdown complete")
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")


def main() -> None:
    """Main entry point for the voice assistant."""
    try:
        assistant = VoiceAssistant()
        assistant.start()
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        raise


if __name__ == "__main__":
    main()
