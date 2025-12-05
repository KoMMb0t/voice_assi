"""Audio processing and component modules for Voice Assistant.

Provides modular components for audio handling, wake word detection,
speech-to-text conversion, and text-to-speech synthesis.
"""

import logging
import time
import json
import os
import asyncio
from typing import Callable, Optional, Tuple
from abc import ABC, abstractmethod
import numpy as np
import sounddevice as sd
import pygame

logger = logging.getLogger(__name__)


class AudioProcessor:
    """Handles audio input from microphone with buffering and monitoring.
    
    Manages audio stream, buffering, and provides callbacks for audio processing.
    Thread-safe and handles device errors gracefully.
    """
    
    def __init__(
        self,
        sample_rate: int = 16000,
        chunk_samples: int = 1280,
        device_index: Optional[int] = None,
        channels: int = 1
    ):
        """Initialize audio processor.
        
        Args:
            sample_rate: Audio sample rate in Hz
            chunk_samples: Number of samples per chunk
            device_index: Audio device index (None = default)
            channels: Number of audio channels
        """
        self.sample_rate = sample_rate
        self.chunk_samples = chunk_samples
        self.device_index = device_index
        self.channels = channels
        
        self._stream: Optional[sd.InputStream] = None
        self._is_recording = False
        self._audio_buffer = []
        
        logger.info(
            f"AudioProcessor initialized: rate={sample_rate}, "
            f"chunk={chunk_samples}, device={device_index}"
        )
    
    def start_stream(self, callback: Callable) -> bool:
        """Start audio stream with callback.
        
        Args:
            callback: Function to call for each audio chunk
            
        Returns:
            True if stream started successfully
        """
        try:
            self._stream = sd.InputStream(
                samplerate=self.sample_rate,
                channels=self.channels,
                dtype='int16',
                blocksize=self.chunk_samples,
                device=self.device_index,
                callback=callback
            )
            self._stream.start()
            self._is_recording = True
            logger.info("Audio stream started")
            return True
        except Exception as e:
            logger.error(f"Failed to start audio stream: {e}")
            return False
    
    def stop_stream(self) -> None:
        """Stop audio stream."""
        if self._stream is not None:
            try:
                self._stream.stop()
                self._stream.close()
                self._is_recording = False
                logger.info("Audio stream stopped")
            except Exception as e:
                logger.error(f"Error stopping audio stream: {e}")
    
    def clear_buffer(self, num_chunks: int) -> None:
        """Clear audio buffer by reading and discarding chunks.
        
        Useful after wake word detection to prevent carryover.
        
        Args:
            num_chunks: Number of chunks to read and discard
        """
        try:
            with sd.InputStream(
                samplerate=self.sample_rate,
                channels=self.channels,
                dtype='int16',
                blocksize=self.chunk_samples,
                device=self.device_index
            ) as stream:
                for _ in range(num_chunks):
                    stream.read(self.chunk_samples)
            logger.debug(f"Audio buffer cleared ({num_chunks} chunks)")
        except Exception as e:
            logger.error(f"Error clearing audio buffer: {e}")
    
    @property
    def is_recording(self) -> bool:
        """Check if currently recording."""
        return self._is_recording


class WakeWordDetector:
    """Detects wake word in audio stream using OpenWakeWord.
    
    Manages wake word model, detection threshold, and cooldown period
    to prevent false positives and double detection.
    """
    
    def __init__(
        self,
        model_name: str = "hey_jarvis",
        threshold: float = 0.5,
        cooldown_seconds: float = 4.0
    ):
        """Initialize wake word detector.
        
        Args:
            model_name: Name of the wake word model
            threshold: Detection threshold (0.0-1.0)
            cooldown_seconds: Cooldown period after detection
        """
        self.model_name = model_name
        self.threshold = threshold
        self.cooldown_seconds = cooldown_seconds
        self._last_detection_time = 0.0
        self._is_paused = False
        
        # Import here to handle optional dependency
        try:
            from openwakeword.model import Model
            self.model = Model(wakeword_models=[model_name])
            logger.info(f"Wake word model loaded: {model_name}")
        except Exception as e:
            logger.error(f"Failed to load wake word model: {e}")
            raise
    
    def detect(self, audio_data: np.ndarray) -> Tuple[bool, float]:
        """Detect wake word in audio data.
        
        Args:
            audio_data: Audio frame as numpy array
            
        Returns:
            Tuple of (detected: bool, confidence: float)
        """
        # Skip detection if in cooldown period
        if self._is_in_cooldown():
            return False, 0.0
        
        # Skip if paused
        if self._is_paused:
            return False, 0.0
        
        try:
            prediction = self.model.predict(audio_data)
            confidence = prediction.get(self.model_name, 0.0)
            
            if confidence > self.threshold:
                logger.info(f"Wake word detected with confidence: {confidence:.2f}")
                self._last_detection_time = time.time()
                return True, confidence
            
            return False, confidence
        except Exception as e:
            logger.error(f"Error during wake word detection: {e}")
            return False, 0.0
    
    def pause(self) -> None:
        """Pause wake word detection."""
        self._is_paused = True
        logger.debug("Wake word detection paused")
    
    def resume(self) -> None:
        """Resume wake word detection."""
        self._is_paused = False
        logger.debug("Wake word detection resumed")
    
    def _is_in_cooldown(self) -> bool:
        """Check if currently in cooldown period."""
        return (time.time() - self._last_detection_time) < self.cooldown_seconds
    
    def reset_cooldown(self) -> None:
        """Manually reset the cooldown timer."""
        self._last_detection_time = 0.0


class SpeechToTextConverter:
    """Converts speech to text using Vosk.
    
    Manages Vosk model, recognition, and handles silence detection
    for determining when recording should stop.
    """
    
    def __init__(
        self,
        language: str = "de",
        silence_timeout: float = 2.0,
        max_record_time: float = 30.0
    ):
        """Initialize speech-to-text converter.
        
        Args:
            language: Language code (e.g., 'de' for German)
            silence_timeout: Timeout for silence detection
            max_record_time: Maximum recording duration
        """
        self.language = language
        self.silence_timeout = silence_timeout
        self.max_record_time = max_record_time
        self._recognizer = None
        
        try:
            from vosk import Model as VoskModel, KaldiRecognizer
            self.VoskModel = VoskModel
            self.KaldiRecognizer = KaldiRecognizer
            
            self.model = VoskModel(lang=language)
            logger.info(f"Vosk model loaded for language: {language}")
        except Exception as e:
            logger.error(f"Failed to load Vosk model: {e}")
            raise
    
    def create_recognizer(self) -> 'KaldiRecognizer':
        """Create a new Kalid recognizer instance.
        
        Returns:
            KaldiRecognizer instance
        """
        recognizer = self.KaldiRecognizer(self.model, 16000)
        recognizer.SetWords(True)
        return recognizer
    
    def recognize(self, audio_data: bytes, recognizer: 'KaldiRecognizer') -> str:
        """Recognize speech from audio data.
        
        Args:
            audio_data: Audio data as bytes
            recognizer: KaldiRecognizer instance
            
        Returns:
            Recognized text or empty string if no match
        """
        try:
            if recognizer.AcceptWaveform(audio_data):
                result = json.loads(recognizer.Result())
            else:
                result = json.loads(recognizer.FinalResult())
            
            text = result.get("text", "").strip()
            
            if text:
                logger.info(f"Speech recognized: '{text}'")
            else:
                logger.debug("No speech recognized")
            
            return text
        except Exception as e:
            logger.error(f"Error during speech recognition: {e}")
            return ""


class TextToSpeechEngine:
    """Text-to-speech synthesis using Edge TTS.
    
    Manages TTS synthesis, audio playback, and cleanup.
    Supports async/await pattern for non-blocking speech.
    """
    
    def __init__(self, voice: str = "de-DE-KatjaNeural"):
        """Initialize TTS engine.
        
        Args:
            voice: Voice identifier (Azure voice format)
        """
        self.voice = voice
        self._is_speaking = False
        
        try:
            import edge_tts
            self.edge_tts = edge_tts
            
            # Initialize pygame mixer for audio playback
            pygame.mixer.init()
            logger.info(f"TTS engine initialized with voice: {voice}")
        except Exception as e:
            logger.error(f"Failed to initialize TTS engine: {e}")
            raise
    
    async def speak_async(self, text: str, temp_file: str = "temp_speech.mp3") -> None:
        """Speak text asynchronously.
        
        Args:
            text: Text to speak
            temp_file: Path for temporary audio file
        """
        try:
            self._is_speaking = True
            logger.info(f"Speaking: {text}")
            
            communicate = self.edge_tts.Communicate(text, self.voice)
            await communicate.save(temp_file)
            
            # Play audio
            pygame.mixer.music.load(temp_file)
            pygame.mixer.music.play()
            
            # Wait for playback to finish
            while pygame.mixer.music.get_busy():
                await asyncio.sleep(0.1)
            
            # Unload and cleanup
            pygame.mixer.music.unload()
            
            # Delete temporary file
            try:
                await asyncio.sleep(0.3)
                if os.path.exists(temp_file):
                    os.remove(temp_file)
            except Exception as e:
                logger.warning(f"Failed to delete temp file: {e}")
            
            self._is_speaking = False
            logger.debug("Speech finished")
        
        except Exception as e:
            logger.error(f"Error during text-to-speech: {e}")
            self._is_speaking = False
    
    def speak(self, text: str) -> None:
        """Speak text synchronously (blocking).
        
        Args:
            text: Text to speak
        """
        asyncio.run(self.speak_async(text))
    
    @property
    def is_speaking(self) -> bool:
        """Check if currently speaking."""
        return self._is_speaking
    
    def cleanup(self) -> None:
        """Cleanup TTS resources."""
        try:
            pygame.mixer.quit()
            logger.info("TTS engine cleaned up")
        except Exception as e:
            logger.error(f"Error cleaning up TTS engine: {e}")
