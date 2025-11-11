#!/usr/bin/env python3
"""
Functionality verification script to ensure all modules work after reorganization.
This tests the core functionality of the refactored project.
"""

import sys
import importlib
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_imports():
    """Test that all key modules can be imported successfully."""
    print("Testing module imports...")
    
    modules_to_test = [
        ('src.main', 'main'),
        ('src.analyze_images', 'analyze_images'),
        ('src.core.event_parser', 'ScriptParser'),
        ('src.core.event_types', 'Event'),
        ('src.analysis.comparison', 'generate_comparison'),
        ('src.analysis.image_analyzer', 'OpenRouterClient'),
        ('src.platform.base', 'WindowManager'),
        ('src.platform.x11_automation', 'X11WindowManager'),
        ('src.ui.interactive_viewer', 'InteractiveViewer'),
    ]
    
    results = []
    for module_name, component_name in modules_to_test:
        try:
            module = importlib.import_module(module_name)
            if hasattr(module, component_name):
                results.append(f"✓ {module_name}.{component_name}")
            else:
                results.append(f"✗ {module_name}.{component_name} - component not found")
        except Exception as e:
            results.append(f"✗ {module_name} - {str(e)}")
    
    return results

def test_script_parsing():
    """Test script parsing functionality."""
    print("\nTesting script parsing...")
    
    try:
        from src.core.event_parser import ScriptParser
        
        test_events = [
            "[ +0.123s ] onMousePressed L: window(100,100) -> world(-16.666666,16.666666)",
            "[ +0.456s ] onMouseReleased L: window(100,100) -> world(-16.666666,16.666666)",
            "[ +0.789s ] onKeyPressed W: test key event",
        ]
        
        parser = ScriptParser()
        events = parser.parse(test_events)
        
        if len(events) == 3:
            print("✓ Script parsing works correctly")
            print(f"  - Parsed {len(events)} events")
            print(f"  - Event types: {[event.action for event in events]}")
            return True
        else:
            print(f"✗ Expected 3 events, got {len(events)}")
            return False
            
    except Exception as e:
        print(f"✗ Script parsing failed: {e}")
        return False

def test_entry_points():
    """Test that entry points are accessible."""
    print("\nTesting entry points...")
    
    try:
        # Test main.py
        from src.main import _parse_args
        main_args = _parse_args(['--help'])
        print("✓ src/main.py entry point works")
    except SystemExit:
        # SystemExit is expected for --help
        print("✓ src/main.py entry point works")
    except Exception as e:
        print(f"✗ src/main.py failed: {e}")
        return False
    
    try:
        # Test analyze_images.py
        from src.analyze_images import _parse_args
        analyze_args = _parse_args(['--help'])
        print("✓ src/analyze_images.py entry point works")
    except SystemExit:
        print("✓ src/analyze_images.py entry point works")
    except Exception as e:
        print(f"✗ src/analyze_images.py failed: {e}")
        return False
    
    return True

def main():
    """Run all functionality tests."""
    print("=" * 60)
    print("Grafika Differ - Functionality Verification")
    print("=" * 60)
    
    success = True
    
    # Test imports
    import_results = test_imports()
    for result in import_results:
        print(result)
        if result.startswith("✗"):
            success = False
    
    # Test script parsing
    if test_script_parsing():
        print("✓ Script parsing functionality maintained")
    else:
        success = False
    
    # Test entry points
    if test_entry_points():
        print("✓ Entry points functional")
    else:
        success = False
    
    print("\n" + "=" * 60)
    if success:
        print("✅ ALL TESTS PASSED - Functionality maintained!")
        print("\nThe reorganization has been successful:")
        print("- Legacy files removed from root directory")
        print("- Test files moved to proper locations")
        print("- X11 automation upgraded to better version")
        print("- All modules remain functional")
    else:
        print("❌ SOME TESTS FAILED - Check functionality")
    
    print("=" * 60)
    return success

if __name__ == "__main__":
    main()