"""Command pattern implementation for Voice Assistant.

Provides base command class and concrete command implementations
for extensible command handling.
"""

import subprocess
import webbrowser
import logging
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class CommandType(Enum):
    """Types of commands."""
    GREETING = "greeting"
    SYSTEM = "system"
    WEB = "web"
    UTILITY = "utility"
    CONTROL = "control"
    HELP = "help"


class BaseCommand(ABC):
    """Abstract base class for all commands.
    
    Defines the interface that all commands must implement.
    """
    
    def __init__(
        self,
        name: str,
        description: str,
        command_type: CommandType,
        keywords: list
    ):
        """Initialize command.
        
        Args:
            name: Command name
            description: Command description
            command_type: Type of command
            keywords: Keywords that trigger this command
        """
        self.name = name
        self.description = description
        self.command_type = command_type
        self.keywords = keywords
        self.last_executed = None
    
    @abstractmethod
    def matches(self, text: str) -> bool:
        """Check if command matches input text.
        
        Args:
            text: Input text to check
            
        Returns:
            True if command matches
        """
        pass
    
    @abstractmethod
    def execute(self) -> str:
        """Execute the command.
        
        Returns:
            Response text to speak
        """
        pass
    
    def log_execution(self) -> None:
        """Log command execution."""
        self.last_executed = datetime.now()
        logger.info(f"Command executed: {self.name}")


class GreetingCommand(BaseCommand):
    """Greeting command."""
    
    def __init__(self):
        """Initialize greeting command."""
        super().__init__(
            name="greeting",
            description="Greet the user",
            command_type=CommandType.GREETING,
            keywords=["hallo", "guten", "morgen", "tag", "abend"]
        )
    
    def matches(self, text: str) -> bool:
        """Check if text contains greeting keywords."""
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in self.keywords)
    
    def execute(self) -> str:
        """Execute greeting."""
        self.log_execution()
        return "Hallo! Wie kann ich helfen?"


class CalcCommand(BaseCommand):
    """Open calculator command."""
    
    def __init__(self):
        """Initialize calculator command."""
        super().__init__(
            name="calculator",
            description="Open the calculator application",
            command_type=CommandType.SYSTEM,
            keywords=["taschenrechner", "rechner", "calc"]
        )
    
    def matches(self, text: str) -> bool:
        """Check if text contains calculator keywords."""
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in self.keywords)
    
    def execute(self) -> str:
        """Execute calculator."""
        try:
            subprocess.Popen("calc.exe")
            self.log_execution()
            logger.info("Calculator opened")
            return "Öffne den Taschenrechner"
        except Exception as e:
            logger.error(f"Failed to open calculator: {e}")
            return "Konnte den Taschenrechner nicht öffnen"


class NotepadCommand(BaseCommand):
    """Open Notepad command."""
    
    def __init__(self):
        """Initialize Notepad command."""
        super().__init__(
            name="notepad",
            description="Open the Notepad application",
            command_type=CommandType.SYSTEM,
            keywords=["editor", "notepad", "notizen"]
        )
    
    def matches(self, text: str) -> bool:
        """Check if text contains Notepad keywords."""
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in self.keywords)
    
    def execute(self) -> str:
        """Execute Notepad."""
        try:
            subprocess.Popen("notepad.exe")
            self.log_execution()
            logger.info("Notepad opened")
            return "Öffne Notepad"
        except Exception as e:
            logger.error(f"Failed to open Notepad: {e}")
            return "Konnte Notepad nicht öffnen"


class ExplorerCommand(BaseCommand):
    """Open File Explorer command."""
    
    def __init__(self):
        """Initialize File Explorer command."""
        super().__init__(
            name="explorer",
            description="Open the File Explorer",
            command_type=CommandType.SYSTEM,
            keywords=["explorer", "dateien", "ordner", "datei"]
        )
    
    def matches(self, text: str) -> bool:
        """Check if text contains Explorer keywords."""
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in self.keywords)
    
    def execute(self) -> str:
        """Execute File Explorer."""
        try:
            subprocess.Popen("explorer.exe")
            self.log_execution()
            logger.info("File Explorer opened")
            return "Öffne den Explorer"
        except Exception as e:
            logger.error(f"Failed to open File Explorer: {e}")
            return "Konnte den Explorer nicht öffnen"


class FirefoxCommand(BaseCommand):
    """Open Firefox command."""
    
    def __init__(self):
        """Initialize Firefox command."""
        super().__init__(
            name="firefox",
            description="Open the Firefox browser",
            command_type=CommandType.WEB,
            keywords=["firefox", "browser"]
        )
    
    def matches(self, text: str) -> bool:
        """Check if text contains Firefox keywords."""
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in self.keywords)
    
    def execute(self) -> str:
        """Execute Firefox."""
        try:
            subprocess.Popen("firefox.exe")
            self.log_execution()
            logger.info("Firefox opened")
            return "Öffne Firefox"
        except FileNotFoundError:
            logger.warning("Firefox not found")
            return "Firefox ist nicht installiert"
        except Exception as e:
            logger.error(f"Failed to open Firefox: {e}")
            return "Konnte Firefox nicht öffnen"


class ChatGPTCommand(BaseCommand):
    """Open ChatGPT command."""
    
    def __init__(self):
        """Initialize ChatGPT command."""
        super().__init__(
            name="chatgpt",
            description="Open ChatGPT in the default browser",
            command_type=CommandType.WEB,
            keywords=["chat", "gpt", "chatgpt"]
        )
    
    def matches(self, text: str) -> bool:
        """Check if text contains ChatGPT keywords."""
        text_lower = text.lower()
        return ("chat" in text_lower and "gpt" in text_lower) or "chatgpt" in text_lower
    
    def execute(self) -> str:
        """Execute ChatGPT."""
        try:
            webbrowser.open("https://chat.openai.com")
            self.log_execution()
            logger.info("ChatGPT opened in browser")
            return "Öffne ChatGPT"
        except Exception as e:
            logger.error(f"Failed to open ChatGPT: {e}")
            return "Konnte ChatGPT nicht öffnen"


class TimeCommand(BaseCommand):
    """Get current time command."""
    
    def __init__(self):
        """Initialize time command."""
        super().__init__(
            name="time",
            description="Tell the current time",
            command_type=CommandType.UTILITY,
            keywords=["uhrzeit", "spät", "spätestens"]
        )
    
    def matches(self, text: str) -> bool:
        """Check if text contains time keywords."""
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in self.keywords)
    
    def execute(self) -> str:
        """Get current time."""
        self.log_execution()
        now = datetime.now()
        time_str = now.strftime("%H:%M")
        return f"Es ist {time_str} Uhr"


class DateCommand(BaseCommand):
    """Get current date command."""
    
    def __init__(self):
        """Initialize date command."""
        super().__init__(
            name="date",
            description="Tell the current date",
            command_type=CommandType.UTILITY,
            keywords=["datum", "tag", "welcher", "heute"]
        )
    
    def matches(self, text: str) -> bool:
        """Check if text contains date keywords."""
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in self.keywords)
    
    def execute(self) -> str:
        """Get current date."""
        self.log_execution()
        now = datetime.now()
        
        date_str = now.strftime("%d. %B %Y")
        weekday = now.strftime("%A")
        
        # Translate weekday to German
        weekdays_de = {
            "Monday": "Montag",
            "Tuesday": "Dienstag",
            "Wednesday": "Mittwoch",
            "Thursday": "Donnerstag",
            "Friday": "Freitag",
            "Saturday": "Samstag",
            "Sunday": "Sonntag"
        }
        weekday_de = weekdays_de.get(weekday, weekday)
        
        return f"Heute ist {weekday_de}, der {date_str}"


class HelpCommand(BaseCommand):
    """Help command."""
    
    def __init__(self):
        """Initialize help command."""
        super().__init__(
            name="help",
            description="Show available commands",
            command_type=CommandType.HELP,
            keywords=["hilfe", "was kannst", "befehle"]
        )
    
    def matches(self, text: str) -> bool:
        """Check if text contains help keywords."""
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in self.keywords)
    
    def execute(self) -> str:
        """Execute help."""
        self.log_execution()
        return "Ich kann Programme öffnen, Webseiten starten, die Uhrzeit sagen und vieles mehr. Frag einfach!"


class CancelCommand(BaseCommand):
    """Cancel/abort current operation."""
    
    def __init__(self):
        """Initialize cancel command."""
        super().__init__(
            name="cancel",
            description="Cancel or abort current operation",
            command_type=CommandType.CONTROL,
            keywords=["abbrechen", "stopp", "stop", "vergiss", "egal", "nichts", "danke"]
        )
    
    def matches(self, text: str) -> bool:
        """Check if text contains cancel keywords."""
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in self.keywords)
    
    def execute(self) -> str:
        """Execute cancel."""
        self.log_execution()
        
        # Different responses based on trigger
        if "danke" in self.last_input:
            return "Gern geschehen!"
        elif "abbrechen" in self.last_input or "stopp" in self.last_input:
            return "Okay, abgebrochen"
        else:
            return "Alles klar"
    
    def set_input(self, text: str) -> None:
        """Set the input text for contextual response."""
        self.last_input = text.lower()


class CommandRegistry:
    """Registry for managing all available commands."""
    
    def __init__(self):
        """Initialize command registry."""
        self.commands: list[BaseCommand] = []
        self._load_default_commands()
    
    def _load_default_commands(self) -> None:
        """Load default commands."""
        self.commands = [
            GreetingCommand(),
            CalcCommand(),
            NotepadCommand(),
            ExplorerCommand(),
            FirefoxCommand(),
            ChatGPTCommand(),
            TimeCommand(),
            DateCommand(),
            HelpCommand(),
            CancelCommand(),
        ]
        logger.info(f"Loaded {len(self.commands)} default commands")
    
    def register_command(self, command: BaseCommand) -> None:
        """Register a new command.
        
        Args:
            command: Command to register
        """
        self.commands.append(command)
        logger.info(f"Command registered: {command.name}")
    
    def find_command(self, text: str) -> Optional[BaseCommand]:
        """Find a command that matches the input text.
        
        Args:
            text: Input text to match
            
        Returns:
            Matching command or None
        """
        for command in self.commands:
            if command.matches(text):
                logger.debug(f"Command matched: {command.name}")
                return command
        
        logger.debug("No command matched")
        return None
    
    def get_commands_by_type(self, command_type: CommandType) -> list[BaseCommand]:
        """Get all commands of a specific type.
        
        Args:
            command_type: Type to filter by
            
        Returns:
            List of matching commands
        """
        return [cmd for cmd in self.commands if cmd.command_type == command_type]
