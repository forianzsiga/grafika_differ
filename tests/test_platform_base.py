"""
Tests for base platform interfaces.
"""

import sys
from pathlib import Path
from abc import ABC, abstractmethod

# Add parent directory to path to import the module
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.platform.base import WindowManager, InputHandler, ScreenshotHandler, ProcessManager


def test_window_manager_interface():
    """Test that WindowManager is abstract and has required methods."""
    # WindowManager should be abstract
    try:
        WindowManager()
        assert False, "WindowManager should be abstract"
    except TypeError:
        pass  # Expected - can't instantiate abstract class
    
    # Check that abstract methods exist
    required_methods = ['find_window_by_title', 'focus_window', 'close_window']
    for method_name in required_methods:
        assert hasattr(WindowManager, method_name)
        # Check that the method is abstract
        method = getattr(WindowManager, method_name)
        assert getattr(method, '__isabstractmethod__', False)


def test_input_handler_interface():
    """Test that InputHandler is abstract and has required methods."""
    # InputHandler should be abstract
    try:
        InputHandler()
        assert False, "InputHandler should be abstract"
    except TypeError:
        pass  # Expected - can't instantiate abstract class
    
    # Check that abstract methods exist
    required_methods = ['move_mouse', 'mouse_press', 'mouse_release', 'send_key', 'send_key_to_window']
    for method_name in required_methods:
        assert hasattr(InputHandler, method_name)
        # Check that the method is abstract
        method = getattr(InputHandler, method_name)
        assert getattr(method, '__isabstractmethod__', False)


def test_screenshot_handler_interface():
    """Test that ScreenshotHandler is abstract and has required methods."""
    # ScreenshotHandler should be abstract
    try:
        ScreenshotHandler()
        assert False, "ScreenshotHandler should be abstract"
    except TypeError:
        pass  # Expected - can't instantiate abstract class
    
    # Check that abstract methods exist
    required_methods = ['capture_window', 'capture_screen']
    for method_name in required_methods:
        assert hasattr(ScreenshotHandler, method_name)
        # Check that the method is abstract
        method = getattr(ScreenshotHandler, method_name)
        assert getattr(method, '__isabstractmethod__', False)


def test_process_manager_interface():
    """Test that ProcessManager is abstract and has required methods."""
    # ProcessManager should be abstract
    try:
        ProcessManager()
        assert False, "ProcessManager should be abstract"
    except TypeError:
        pass  # Expected - can't instantiate abstract class
    
    # Check that abstract methods exist
    required_methods = ['is_process_running', 'terminate_process', 'kill_process']
    for method_name in required_methods:
        assert hasattr(ProcessManager, method_name)
        # Check that the method is abstract
        method = getattr(ProcessManager, method_name)
        assert getattr(method, '__isabstractmethod__', False)


def test_concrete_implementation():
    """Test that we can create a concrete implementation."""
    from src.platform.base import WindowManager, InputHandler, ScreenshotHandler, ProcessManager
    
    class MockWindowManager(WindowManager):
        def find_window_by_title(self, title_pattern: str):
            return 12345
        
        def focus_window(self, window_id: int):
            return True
        
        def close_window(self, window_id: int):
            return True
    
    class MockInputHandler(InputHandler):
        def move_mouse(self, x: int, y: int, duration: float = 0.0):
            return True
        
        def mouse_press(self, button: str = "left"):
            return True
        
        def mouse_release(self, button: str = "left"):
            return True
        
        def send_key(self, key_sym_str: str):
            return True
        
        def send_key_to_window(self, window_id: int, key_sym_str: str):
            return True
    
    class MockScreenshotHandler(ScreenshotHandler):
        def capture_window(self, window_id: int, output_path: Path):
            return True
        
        def capture_screen(self, output_path: Path):
            return True
    
    class MockProcessManager(ProcessManager):
        def is_process_running(self, pid: int):
            return True
        
        def terminate_process(self, pid: int):
            return True
        
        def kill_process(self, pid: int):
            return True
    
    # Test that concrete implementations work
    wm = MockWindowManager()
    assert wm.find_window_by_title("test") == 12345
    assert wm.focus_window(12345) == True
    assert wm.close_window(12345) == True
    
    ih = MockInputHandler()
    assert ih.move_mouse(100, 200) == True
    assert ih.mouse_press() == True
    assert ih.mouse_release() == True
    assert ih.send_key("A") == True
    assert ih.send_key_to_window(12345, "B") == True
    
    sh = MockScreenshotHandler()
    assert sh.capture_window(12345, Path("test.png")) == True
    assert sh.capture_screen(Path("screen.png")) == True
    
    pm = MockProcessManager()
    assert pm.is_process_running(12345) == True
    assert pm.terminate_process(12345) == True
    assert pm.kill_process(12345) == True


if __name__ == "__main__":
    print("Testing platform base interfaces...")
    
    test_window_manager_interface()
    print("✓ WindowManager interface test passed")
    
    test_input_handler_interface()
    print("✓ InputHandler interface test passed")
    
    test_screenshot_handler_interface()
    print("✓ ScreenshotHandler interface test passed")
    
    test_process_manager_interface()
    print("✓ ProcessManager interface test passed")
    
    test_concrete_implementation()
    print("✓ Concrete implementation test passed")
    
    print("\nAll platform base interface tests passed!")
