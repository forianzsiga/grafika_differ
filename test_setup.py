#!/usr/bin/env python3
"""
Test script for image_analysis_openrouter.py

This script verifies the setup and demonstrates basic functionality
without requiring actual screenshot directories.
"""

import os
import sys
from pathlib import Path

# Color codes for terminal output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

def print_header(text):
    print(f"\n{BLUE}{'=' * 60}{RESET}")
    print(f"{BLUE}{text}{RESET}")
    print(f"{BLUE}{'=' * 60}{RESET}\n")

def print_success(text):
    print(f"{GREEN}✓{RESET} {text}")

def print_error(text):
    print(f"{RED}✗{RESET} {text}")

def print_warning(text):
    print(f"{YELLOW}⚠{RESET} {text}")

def print_info(text):
    print(f"  {text}")

def check_dependencies():
    """Check if required dependencies are installed."""
    print_header("Checking Dependencies")
    
    all_ok = True
    
    # Check requests
    try:
        import requests
        print_success("requests library is installed")
    except ImportError:
        print_error("requests library is NOT installed")
        print_info("Install with: pip install requests")
        all_ok = False
    
    # Check PIL
    try:
        from PIL import Image
        print_success("Pillow (PIL) library is installed")
    except ImportError:
        print_error("Pillow (PIL) library is NOT installed")
        print_info("Install with: pip install pillow")
        all_ok = False
    
    return all_ok

def check_api_key():
    """Check if OpenRouter API key is configured."""
    print_header("Checking API Key Configuration")
    
    api_key = os.environ.get("OPENROUTER_API_KEY")
    
    if api_key:
        # Mask the key for display
        masked = api_key[:10] + "..." + api_key[-4:] if len(api_key) > 14 else "***"
        print_success(f"OPENROUTER_API_KEY is set: {masked}")
        return True
    else:
        print_error("OPENROUTER_API_KEY is NOT set")
        print_info("Set it with: export OPENROUTER_API_KEY='your_key_here'")
        print_info("Get a key from: https://openrouter.ai/")
        return False

def check_script_exists():
    """Check if the main script exists."""
    print_header("Checking Main Script")
    
    script_path = Path(__file__).parent / "image_analysis_openrouter.py"
    
    if script_path.exists():
        print_success(f"Main script found: {script_path}")
        return True
    else:
        print_error(f"Main script NOT found: {script_path}")
        return False

def check_example_directories():
    """Check for example screenshot directories."""
    print_header("Checking for Example Data")
    
    base_dir = Path(__file__).parent
    screenshot_dirs = [
        base_dir / "screenshots",
        base_dir / "screenshots" / "run01",
        base_dir / "screenshots" / "run02",
        base_dir / "screenshots" / "comparison01"
    ]
    
    found = []
    for dir_path in screenshot_dirs:
        if dir_path.exists() and dir_path.is_dir():
            png_count = len(list(dir_path.glob("*.png")))
            if png_count > 0:
                print_success(f"Found {dir_path.name} with {png_count} PNG files")
                found.append(dir_path)
            else:
                print_warning(f"Found {dir_path.name} but it's empty")
        else:
            print_info(f"Not found: {dir_path.name}")
    
    return found

def demonstrate_usage():
    """Show usage examples."""
    print_header("Usage Examples")
    
    print("Basic usage:")
    print_info("python image_analysis_openrouter.py \\")
    print_info("    --inputs screenshots/run01 screenshots/run02 \\")
    print_info("    --output analysis_results")
    print()
    
    print("With difference directory:")
    print_info("python image_analysis_openrouter.py \\")
    print_info("    --inputs screenshots/run01 screenshots/run02 \\")
    print_info("    --diff-dir screenshots/comparison01 \\")
    print_info("    --output analysis_results")
    print()
    
    print("Using the automation script:")
    print_info("./analyze_differences.sh \\")
    print_info("    -a screenshots/run01 \\")
    print_info("    -b screenshots/run02 \\")
    print_info("    -o analysis_results")
    print()

def test_api_connection():
    """Test connection to OpenRouter API (if key is available)."""
    print_header("Testing API Connection")
    
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        print_warning("Skipping API test (no API key)")
        return False
    
    try:
        import requests
        
        print_info("Sending test request to OpenRouter API...")
        
        response = requests.get(
            "https://openrouter.ai/api/v1/models",
            headers={
                "Authorization": f"Bearer {api_key}",
            },
            timeout=10
        )
        
        if response.status_code == 200:
            print_success("API connection successful!")
            models = response.json().get('data', [])
            print_info(f"Found {len(models)} available models")
            
            # Show a few vision-capable models
            vision_models = [m for m in models if 'vision' in m.get('id', '').lower() 
                           or 'gemini' in m.get('id', '').lower()]
            if vision_models:
                print_info("Some available vision models:")
                for model in vision_models[:5]:
                    print_info(f"  - {model.get('id', 'unknown')}")
            
            return True
        else:
            print_error(f"API returned status code: {response.status_code}")
            print_info(f"Response: {response.text[:200]}")
            return False
            
    except ImportError:
        print_error("requests library not available")
        return False
    except Exception as e:
        print_error(f"API test failed: {e}")
        return False

def main():
    """Run all checks."""
    print()
    print(f"{BLUE}╔═══════════════════════════════════════════════════════════╗{RESET}")
    print(f"{BLUE}║  Image Analysis OpenRouter - Setup Verification          ║{RESET}")
    print(f"{BLUE}╚═══════════════════════════════════════════════════════════╝{RESET}")
    
    results = {
        "Dependencies": check_dependencies(),
        "API Key": check_api_key(),
        "Main Script": check_script_exists(),
    }
    
    # Check example data
    example_dirs = check_example_directories()
    results["Example Data"] = len(example_dirs) > 0
    
    # Test API connection if possible
    if results["Dependencies"] and results["API Key"]:
        results["API Connection"] = test_api_connection()
    
    # Show usage examples
    demonstrate_usage()
    
    # Summary
    print_header("Setup Summary")
    
    all_passed = True
    for check, passed in results.items():
        if passed:
            print_success(f"{check}: OK")
        else:
            print_error(f"{check}: FAILED")
            all_passed = False
    
    print()
    if all_passed:
        print(f"{GREEN}{'=' * 60}{RESET}")
        print(f"{GREEN}All checks passed! You're ready to use the image analyzer.{RESET}")
        print(f"{GREEN}{'=' * 60}{RESET}")
        
        if example_dirs:
            print()
            print("You can try analyzing the example screenshots:")
            print_info(f"python image_analysis_openrouter.py \\")
            print_info(f"    --inputs {example_dirs[0]} {example_dirs[1] if len(example_dirs) > 1 else example_dirs[0]} \\")
            print_info(f"    --output test_analysis")
        
        return 0
    else:
        print(f"{RED}{'=' * 60}{RESET}")
        print(f"{RED}Some checks failed. Please fix the issues above.{RESET}")
        print(f"{RED}{'=' * 60}{RESET}")
        print()
        print("Quick fixes:")
        
        if not results["Dependencies"]:
            print_info("Install dependencies: pip install -r requirements.txt")
        
        if not results["API Key"]:
            print_info("Set API key: export OPENROUTER_API_KEY='your_key_here'")
            print_info("Get key from: https://openrouter.ai/")
        
        return 1

if __name__ == "__main__":
    sys.exit(main())
