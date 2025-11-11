"""
Tests for event parsing functionality.
"""

import sys
from pathlib import Path

# Add parent directory to path to import the module
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.event_parser import ScriptParser


def test_parse_mouse_events():
    """Test parsing of mouse events."""
    parser = ScriptParser()
    
    lines = [
        "[ +0.123s ] onMousePressed L: window(100,100) -> world(-16.666666,16.666666)",
        "[ +0.456s ] onMouseReleased R: window(150,200) -> world(-10.0,5.0)",
    ]
    
    events = parser.parse(lines)
    
    assert len(events) == 2
    
    # First event - mouse press left
    event1 = events[0]
    assert event1.index == 0
    assert event1.timestamp == 0.123
    assert event1.action == "mouse_press"
    assert event1.button == "left"
    assert event1.window_point == (100, 100)
    assert event1.world_point == (-16.666666, 16.666666)
    
    # Second event - mouse release right
    event2 = events[1]
    assert event2.index == 1
    assert event2.timestamp == 0.456
    assert event2.action == "mouse_release"
    assert event2.button == "right"
    assert event2.window_point == (150, 200)
    assert event2.world_point == (-10.0, 5.0)


def test_parse_keyboard_events():
    """Test parsing of keyboard events."""
    parser = ScriptParser()
    
    lines = [
        "[ +0.123s ] onKeyPressed D: test key press",
        "[ +0.456s ] onKeyReleased W: test key release",
        "[ +0.789s ] onKeyPressed 1: number key",
    ]
    
    events = parser.parse(lines)
    
    assert len(events) == 3
    
    # First event - key press D
    event1 = events[0]
    assert event1.action == "key_press"
    assert event1.button == "D"
    
    # Second event - key release W
    event2 = events[1]
    assert event2.action == "key_release"
    assert event2.button == "W"
    
    # Third event - number key
    event3 = events[2]
    assert event3.action == "key_press"
    assert event3.button == "1"


def test_parse_exit_event():
    """Test parsing of application exit event."""
    parser = ScriptParser()
    
    lines = [
        "[ +10.500s ] Exiting application"
    ]
    
    events = parser.parse(lines)
    
    assert len(events) == 1
    event = events[0]
    assert event.action == "exit"
    assert event.button is None
    assert event.window_point is None
    assert event.world_point is None


def test_delta_assignment():
    """Test that deltas are correctly assigned between events."""
    parser = ScriptParser()
    
    lines = [
        "[ +1.000s ] onMousePressed L: first event",
        "[ +1.500s ] onMouseReleased L: second event (0.5s later)",
        "[ +2.200s ] onMousePressed R: third event (0.7s later)",
    ]
    
    events = parser.parse(lines)
    
    assert len(events) == 3
    
    # First event has no previous event, delta should be 1.0 (timestamp - 0)
    assert events[0].delta == 1.0
    
    # Second event is 0.5s after first (1.5 - 1.0 = 0.5)
    assert events[1].delta == 0.5
    
    # Third event is 0.7s after second (2.2 - 1.5 = 0.7)
    assert abs(events[2].delta - 0.7) < 0.001  # Use approximate comparison for floating point


def test_empty_lines_skipped():
    """Test that empty lines are skipped during parsing."""
    parser = ScriptParser()
    
    lines = [
        "[ +0.123s ] onMousePressed L: first event",
        "",  # Empty line should be skipped
        "   ",  # Whitespace only should be skipped
        "[ +0.456s ] onKeyPressed D: second event",
    ]
    
    events = parser.parse(lines)
    
    assert len(events) == 2
    assert events[0].action == "mouse_press"
    assert events[1].action == "key_press"


def test_invalid_line_raises_error():
    """Test that invalid event lines raise ValueError."""
    parser = ScriptParser()
    
    invalid_lines = [
        "This is not a valid event line",
        "[ invalid timestamp format ] onMousePressed L: test",
        "[ +0.123s ] unsupported event type: test",
    ]
    
    for line in invalid_lines:
        try:
            parser.parse([line])
            assert False, f"Should have raised ValueError for line: {line}"
        except ValueError:
            pass  # Expected


if __name__ == "__main__":
    print("Testing event parser...")
    
    test_parse_mouse_events()
    print("✓ Mouse event parsing test passed")
    
    test_parse_keyboard_events()
    print("✓ Keyboard event parsing test passed")
    
    test_parse_exit_event()
    print("✓ Exit event parsing test passed")
    
    test_delta_assignment()
    print("✓ Delta assignment test passed")
    
    test_empty_lines_skipped()
    print("✓ Empty lines skipping test passed")
    
    test_invalid_line_raises_error()
    print("✓ Invalid line error handling test passed")
    
    print("\nAll event parser tests passed!")
