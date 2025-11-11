"""Event definitions for automation framework."""

from dataclasses import dataclass
from typing import Optional, Tuple


@dataclass
class Event:
    """Represents a recorded UI interaction event."""
    
    index: int
    timestamp: float
    delta: float
    action: str
    button: Optional[str]
    window_point: Optional[Tuple[int, int]]
    world_point: Optional[Tuple[float, float]]
    raw: str

    def label(self) -> str:
        """Get a human-readable label for this event."""
        base = self.action
        if self.button:
            base = f"{base}_{self.button}"
        return base
