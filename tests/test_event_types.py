"""
Tests for event types and event handling.
"""

import sys
from pathlib import Path

# Add parent directory to path to import the module
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from core.event_types import Event


def test_event_creation():
    """Test Event dataclass creation and basic attributes."""
    event = Event(
        index=1,
        timestamp=1.5,
        delta=0.1,
        action="mouse_press",
        button="left",
        window_point=(100, 200),
        world_point=(10.5, -5.2),
        raw="[ +1.500s ] onMousePressed L: test event"
    )
    
    assert event.index == 1
    assert event.timestamp == 1.5
    assert event.delta == 0.1
    assert event.action == "mouse_press"
    assert event.button == "left"
    assert event.window_point == (100, 200)
    assert event.world_point == (10.5, -5.2)
    assert event.raw == "[ +1.500s ] onMousePressed L: test event"


def test_event_label():
    """Test Event label generation."""
    # Test mouse event with button
    mouse_event = Event(0, 0, 0, "mouse_press", "left", None, None, "")
    assert mouse_event.label() == "mouse_press_left"
    
    mouse_release = Event(0, 0, 0, "mouse_release", "right", None, None, "")
    assert mouse_release.label() == "mouse_release_right"
    
    # Test keyboard event
    key_event = Event(0, 0, 0, "key_press", "A", None, None, "")
    assert key_event.label() == "key_press_A"
    
    # Test event without button
    exit_event = Event(0, 0, 0, "exit", None, None, None, "")
    assert exit_event.label() == "exit"


def test_event_with_none_values():
    """Test Event creation with None values for optional fields."""
    event = Event(
        index=0,
        timestamp=0.0,
        delta=0.0,
        action="exit",
        button=None,
        window_point=None,
        world_point=None,
        raw="[ +0.000s ] Exiting application"
    )
    
    assert event.button is None
    assert event.window_point is None
    assert event.world_point is None
    assert event.label() == "exit"


if __name__ == "__main__":
    print("Testing event types...")
    
    test_event_creation()
    print("✓ Event creation test passed")
    
    test_event_label()
    print("✓ Event label test passed")
    
    test_event_with_none_values()
    print("✓ Event with None values test passed")
    
    print("\nAll event type tests passed!")
