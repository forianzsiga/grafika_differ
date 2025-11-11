"""
Integration tests for the refactored grafika_differ package.

This test verifies that the refactored modules can be imported and used together.
"""

import sys
from pathlib import Path

# Add parent directory to path to import the module
sys.path.insert(0, str(Path(__file__).parent.parent))


def test_core_module_imports():
    """Test that core modules can be imported successfully."""
    try:
        from src.core import Event, ScriptParser, AutomationRunner
        print("✓ Core modules import successfully")
    except ImportError as e:
        print(f"✗ Core module import failed: {e}")
        return False
    return True


def test_platform_module_imports():
    """Test that platform modules can be imported successfully."""
    try:
        from src.platform import (
            WindowManager, InputHandler, ScreenshotHandler, ProcessManager,
            setup_linux_environment
        )
        print("✓ Platform modules import successfully")
    except ImportError as e:
        print(f"✗ Platform module import failed: {e}")
        return False
    return True


def test_analysis_module_imports():
    """Test that analysis modules can be imported successfully."""
    try:
        from src.analysis import OpenRouterClient, ImageAnalyzer, generate_comparison
        print("✓ Analysis modules import successfully")
    except ImportError as e:
        print(f"✗ Analysis module import failed: {e}")
        return False
    return True


def test_ui_module_imports():
    """Test that UI modules can be imported successfully."""
    try:
        from src.ui import InteractiveViewer
        print("✓ UI modules import successfully")
    except ImportError as e:
        print(f"✗ UI module import failed: {e}")
        return False
    return True


def test_event_parser_integration():
    """Test that event parser works with event types."""
    try:
        from src.core.event_parser import ScriptParser
        from src.core.event_types import Event
        
        # Parse some test events
        parser = ScriptParser()
        lines = [
            "[ +0.123s ] onMousePressed L: window(100,100) -> world(-16.666666,16.666666)",
            "[ +0.456s ] onKeyPressed D: test key",
        ]
        
        events = parser.parse(lines)
        
        assert len(events) == 2
        assert isinstance(events[0], Event)
        assert events[0].action == "mouse_press"
        assert events[0].button == "left"
        assert events[1].action == "key_press"
        assert events[1].button == "D"
        
        print("✓ Event parser integration test passed")
        return True
    except Exception as e:
        print(f"✗ Event parser integration test failed: {e}")
        return False


def test_package_structure():
    """Test that the package structure is correct."""
    base_path = Path(__file__).parent.parent / "src"
    
    # Check main package
    assert (base_path / "__init__.py").exists()
    
    # Check subpackages
    subpackages = ["core", "platform", "analysis", "ui", "utils"]
    for subpackage in subpackages:
        package_path = base_path / subpackage
        assert package_path.exists()
        assert (package_path / "__init__.py").exists()
    
    print("✓ Package structure test passed")
    return True


def test_automation_config():
    """Test AutomationConfig creation and usage."""
    try:
        from src.core.automation_runner import AutomationConfig
        
        config = AutomationConfig(
            exe_path=Path("/fake/path"),
            window_title="Test Window",
            screenshot_dir=Path("/fake/screenshots"),
            launch_wait=1.5,
            window_timeout=15.0,
            exit_timeout=10.0,
            pointer_duration=0.0,
            capture_delay=0.0
        )
        
        assert config.exe_path == Path("/fake/path")
        assert config.window_title == "Test Window"
        assert config.launch_wait == 1.5
        
        print("✓ AutomationConfig test passed")
        return True
    except Exception as e:
        print(f"✗ AutomationConfig test failed: {e}")
        return False


def test_linux_environment_check():
    """Test Linux environment validation."""
    try:
        from src.platform.x11_automation import check_x11_dependencies, setup_linux_environment
        
        # This should work even if X11 is not available
        missing = check_x11_dependencies()
        assert isinstance(missing, list)
        
        # setup_linux_environment will return False if not on Linux or if missing deps
        result = setup_linux_environment()
        assert isinstance(result, bool)
        
        print("✓ Linux environment check test passed")
        return True
    except Exception as e:
        print(f"✗ Linux environment check test failed: {e}")
        return False


def test_main_package():
    """Test that main package can be imported."""
    try:
        import src
        assert hasattr(src, "__version__")
        assert hasattr(src, "__author__")
        print("✓ Main package import test passed")
        return True
    except Exception as e:
        print(f"✗ Main package import test failed: {e}")
        return False


def main():
    """Run all integration tests."""
    print("Running integration tests for refactored grafika_differ package")
    print("=" * 70)
    
    tests = [
        test_package_structure,
        test_main_package,
        test_core_module_imports,
        test_platform_module_imports,
        test_analysis_module_imports,
        test_ui_module_imports,
        test_event_parser_integration,
        test_automation_config,
        test_linux_environment_check,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"✗ Test {test.__name__} failed with exception: {e}")
            failed += 1
    
    print("\n" + "=" * 70)
    print(f"Integration test results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All integration tests passed! Refactoring successful!")
    else:
        print("⚠ Some integration tests failed. Please review the issues above.")
    
    return failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
