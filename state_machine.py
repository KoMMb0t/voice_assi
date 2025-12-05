"""State machine and event system for Voice Assistant.

Provides a robust state machine implementation with proper state transitions
and event handling to prevent race conditions and double wake-word detection.
"""

from enum import Enum, auto
from typing import Callable, Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class AssistantState(Enum):
    """Enumeration of possible assistant states."""
    
    IDLE = auto()                    # Waiting for wake word
    LISTENING_FOR_COMMAND = auto()   # Recording user command
    PROCESSING_COMMAND = auto()      # Processing the recognized command
    SPEAKING = auto()               # Playing TTS response
    COOLDOWN = auto()               # In cooldown period (preventing double detection)
    ERROR = auto()                  # Error state
    SHUTDOWN = auto()               # Shutting down


class AssistantEvent(Enum):
    """Enumeration of events that can occur in the assistant."""
    
    # Wake word events
    WAKE_WORD_DETECTED = auto()
    
    # Audio/Recording events
    RECORDING_STARTED = auto()
    RECORDING_FINISHED = auto()
    AUDIO_ERROR = auto()
    
    # Command processing events
    COMMAND_RECOGNIZED = auto()
    COMMAND_EXECUTED = auto()
    COMMAND_FAILED = auto()
    
    # TTS events
    SPEECH_STARTED = auto()
    SPEECH_FINISHED = auto()
    
    # System events
    COOLDOWN_FINISHED = auto()
    SHUTDOWN_REQUESTED = auto()
    ERROR_OCCURRED = auto()


@dataclass
class Event:
    """Represents a single event in the assistant."""
    
    event_type: AssistantEvent
    timestamp: datetime
    data: Optional[Dict[str, Any]] = None
    
    def __init__(self, event_type: AssistantEvent, data: Optional[Dict[str, Any]] = None):
        """Initialize event."""
        self.event_type = event_type
        self.timestamp = datetime.now()
        self.data = data or {}


class StateMachine:
    """State machine for managing assistant state transitions.
    
    Ensures proper state transitions and prevents invalid state combinations.
    Handles state change callbacks and maintains transition history.
    """
    
    def __init__(self):
        """Initialize state machine."""
        self._current_state = AssistantState.IDLE
        self._previous_state = AssistantState.IDLE
        self._state_change_callbacks: Dict[AssistantState, List[Callable]] = {}
        self._event_history: List[Event] = []
        self._max_history_size = 100
        logger.info(f"StateMachine initialized in {self._current_state.name} state")
    
    @property
    def current_state(self) -> AssistantState:
        """Get the current state."""
        return self._current_state
    
    @property
    def previous_state(self) -> AssistantState:
        """Get the previous state."""
        return self._previous_state
    
    def can_transition(self, target_state: AssistantState) -> bool:
        """Check if transition to target state is allowed.
        
        Args:
            target_state: The target state to transition to
            
        Returns:
            True if transition is allowed, False otherwise
        """
        # Define valid state transitions
        valid_transitions = {
            AssistantState.IDLE: [
                AssistantState.LISTENING_FOR_COMMAND,
                AssistantState.SHUTDOWN,
                AssistantState.ERROR,
            ],
            AssistantState.LISTENING_FOR_COMMAND: [
                AssistantState.PROCESSING_COMMAND,
                AssistantState.IDLE,
                AssistantState.ERROR,
            ],
            AssistantState.PROCESSING_COMMAND: [
                AssistantState.SPEAKING,
                AssistantState.IDLE,
                AssistantState.COOLDOWN,
                AssistantState.ERROR,
            ],
            AssistantState.SPEAKING: [
                AssistantState.COOLDOWN,
                AssistantState.IDLE,
                AssistantState.ERROR,
            ],
            AssistantState.COOLDOWN: [
                AssistantState.IDLE,
                AssistantState.ERROR,
            ],
            AssistantState.ERROR: [
                AssistantState.IDLE,
                AssistantState.SHUTDOWN,
            ],
            AssistantState.SHUTDOWN: [],
        }
        
        allowed = valid_transitions.get(self._current_state, [])
        return target_state in allowed
    
    def transition(self, target_state: AssistantState) -> bool:
        """Transition to a new state.
        
        Args:
            target_state: The target state to transition to
            
        Returns:
            True if transition was successful, False if invalid
        """
        if not self.can_transition(target_state):
            logger.warning(
                f"Invalid state transition: {self._current_state.name} -> {target_state.name}"
            )
            return False
        
        self._previous_state = self._current_state
        self._current_state = target_state
        logger.info(
            f"State transition: {self._previous_state.name} -> {self._current_state.name}"
        )
        
        # Execute callbacks for new state
        self._execute_callbacks(target_state)
        
        return True
    
    def on_state_change(self, state: AssistantState, callback: Callable) -> None:
        """Register a callback for state changes.
        
        Args:
            state: The state to listen for
            callback: Callable to execute when state is entered
        """
        if state not in self._state_change_callbacks:
            self._state_change_callbacks[state] = []
        
        self._state_change_callbacks[state].append(callback)
    
    def _execute_callbacks(self, state: AssistantState) -> None:
        """Execute all callbacks registered for a state.
        
        Args:
            state: The state whose callbacks should be executed
        """
        callbacks = self._state_change_callbacks.get(state, [])
        for callback in callbacks:
            try:
                callback()
            except Exception as e:
                logger.error(f"Error executing state change callback: {e}")
    
    def record_event(self, event: Event) -> None:
        """Record an event in the history.
        
        Args:
            event: The event to record
        """
        self._event_history.append(event)
        
        # Keep history size manageable
        if len(self._event_history) > self._max_history_size:
            self._event_history.pop(0)
    
    def get_event_history(self) -> List[Event]:
        """Get the event history.
        
        Returns:
            List of recorded events
        """
        return self._event_history.copy()
    
    def reset(self) -> None:
        """Reset state machine to IDLE state."""
        self._current_state = AssistantState.IDLE
        self._previous_state = AssistantState.IDLE
        self._event_history.clear()
        logger.info("State machine reset to IDLE")


class EventBus:
    """Event bus for publishing and subscribing to events.
    
    Provides decoupled communication between components via events.
    """
    
    def __init__(self):
        """Initialize event bus."""
        self._subscribers: Dict[AssistantEvent, List[Callable]] = {}
        self._event_history: List[Event] = []
        self._max_history_size = 100
    
    def subscribe(self, event_type: AssistantEvent, handler: Callable) -> None:
        """Subscribe to an event type.
        
        Args:
            event_type: The event type to subscribe to
            handler: Callable to handle the event
        """
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        
        self._subscribers[event_type].append(handler)
        logger.debug(f"Subscribed to {event_type.name}")
    
    def unsubscribe(self, event_type: AssistantEvent, handler: Callable) -> None:
        """Unsubscribe from an event type.
        
        Args:
            event_type: The event type to unsubscribe from
            handler: The handler to remove
        """
        if event_type in self._subscribers:
            self._subscribers[event_type].remove(handler)
            logger.debug(f"Unsubscribed from {event_type.name}")
    
    def publish(self, event: Event) -> None:
        """Publish an event to all subscribers.
        
        Args:
            event: The event to publish
        """
        self._event_history.append(event)
        
        # Keep history size manageable
        if len(self._event_history) > self._max_history_size:
            self._event_history.pop(0)
        
        handlers = self._subscribers.get(event.event_type, [])
        logger.debug(f"Publishing {event.event_type.name} to {len(handlers)} subscribers")
        
        for handler in handlers:
            try:
                handler(event)
            except Exception as e:
                logger.error(f"Error in event handler for {event.event_type.name}: {e}")
    
    def get_event_history(self) -> List[Event]:
        """Get the event history.
        
        Returns:
            List of recorded events
        """
        return self._event_history.copy()
