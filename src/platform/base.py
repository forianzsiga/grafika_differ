"""Base platform classes for cross-platform automation support."""

from abc import ABC, abstractmethod
from typing import List, Optional, Tuple
from pathlib import Path


class WindowManager(ABC):
    """Abstract interface for window management across platforms."""
    
    @abstractmethod
    def find_window_by_title(self, title_pattern: str) -> Optional[int]:
        """Find window by title pattern."""
        pass
    
    @abstractmethod
    def focus_window(self, window_id: int) -> bool:
        """Focus a specific window."""
        pass
    
    @abstractmethod
    def close_window(self, window_id: int) -> bool:
        """Close a specific window."""
        pass


class InputHandler(ABC):
    """Abstract interface for input simulation across platforms."""
    
    @abstractmethod
    def move_mouse(self, x: int, y: int, duration: float = 0.0) -> bool:
        """Move mouse to coordinates."""
        pass
    
    @abstractmethod
    def mouse_press(self, button: str = "left") -> bool:
        """Press mouse button."""
        pass
    
    @abstractmethod
    def mouse_release(self, button: str = "left") -> bool:
        """Release mouse button."""
        pass
    
    @abstractmethod
    def send_key(self, key_sym_str: str) -> bool:
        """Send keyboard input."""
        pass
    
    @abstractmethod
    def send_key_to_window(self, window_id: int, key_sym_str: str) -> bool:
        """Send keyboard input to specific window."""
        pass


class ScreenshotHandler(ABC):
    """Abstract interface for screenshot capture across platforms."""
    
    @abstractmethod
    def capture_window(self, window_id: int, output_path: Path) -> bool:
        """Capture screenshot of specific window."""
        pass
    
    @abstractmethod
    def capture_screen(self, output_path: Path) -> bool:
        """Capture full screen screenshot."""
        pass


class ProcessManager(ABC):
    """Abstract interface for process management across platforms."""
    
    @abstractmethod
    def is_process_running(self, pid: int) -> bool:
        """Check if process is running."""
        pass
    
    @abstractmethod
    def terminate_process(self, pid: int) -> bool:
        """Terminate process gracefully."""
        pass
    
    @abstractmethod
    def kill_process(self, pid: int) -> bool:
        """Force kill process."""
        pass
