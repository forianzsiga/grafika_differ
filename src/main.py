#!/usr/bin/env python3
"""Main entry point for automation framework."""

import argparse
import logging
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core import ScriptParser, AutomationRunner, AutomationConfig
from src.analysis import generate_comparison
from src.ui import InteractiveViewer


def _configure_pyautogui():
    """Configure pyautogui for safe automation."""
    try:
        import pyautogui
        pyautogui.FAILSAFE = False
        pyautogui.PAUSE = 0.0
    except ImportError:
        pass


def _parse_args(argv=None):
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Cross-platform automation framework for replaying recorded UI scripts."
    )
    parser.add_argument(
        "--mode",
        choices=["script", "comparison", "interactive", "stealth"],
        default="script",
        help=(
            "Execution mode: 'script' replays events, 'comparison' diffs two runs, "
            "'interactive' opens viewer, 'stealth' captures frames at fixed intervals"
        ),
    )
    parser.add_argument("--script", type=Path, help="Path to the recorded event transcript")
    parser.add_argument("--exe", type=Path, help="Path to the target executable")
    parser.add_argument("positional_exe", nargs="?", type=Path, help=argparse.SUPPRESS)
    parser.add_argument("--window-title", dest="window_title", help="Window title to focus; defaults to top window")
    parser.add_argument("--screenshots", type=Path, default=Path("screenshots"), help="Directory where screenshots will be stored")
    parser.add_argument("--output", type=Path, help="Directory where mode-specific outputs will be written")
    parser.add_argument("--inputs", nargs="+", type=Path, help="Input directories for comparison/interactive modes")
    parser.add_argument("--launch-wait", type=float, default=1.5, help="Extra seconds to wait after window becomes ready")
    parser.add_argument("--window-timeout", type=float, default=15.0, help="Seconds to wait for main window to appear")
    parser.add_argument("--exit-timeout", type=float, default=10.0, help="Seconds to wait for process to exit")
    parser.add_argument("--pointer-duration", type=float, default=0.0, help="Duration in seconds for mouse move animations")
    parser.add_argument("--capture-delay", type=float, default=0.0, help="Extra delay before each screenshot")
    parser.add_argument("--delta", type=int, default=50, help="Stealth mode: capture interval in milliseconds")
    parser.add_argument("--length", type=int, default=5000, help="Stealth mode: total capture duration in milliseconds")
    parser.add_argument("--log-level", choices=["DEBUG", "INFO", "WARNING", "ERROR"], default="INFO", help="Console log verbosity")
    
    return parser.parse_args(argv)


def main(argv=None):
    """Main entry point."""
    args = _parse_args(argv)
    
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(asctime)s %(levelname)s %(message)s"
    )
    
    # Handle interactive mode
    if args.mode == "interactive":
        if not args.inputs or len(args.inputs) < 2:
            raise SystemExit("Interactive mode requires --inputs with 2 (optionally 3) directories")
        try:
            viewer = InteractiveViewer(list(args.inputs))
            viewer.run()
        except KeyboardInterrupt:
            logging.info("Viewer interrupted by user")
            sys.exit(0)
        return
    
    # Handle comparison mode
    if args.mode == "comparison":
        if not args.inputs:
            raise SystemExit("Comparison mode requires exactly two --inputs directories")
        if args.output is None:
            raise SystemExit("Comparison mode requires an --output directory")
        try:
            generate_comparison(list(args.inputs), args.output)
        except KeyboardInterrupt:
            logging.info("Comparison interrupted by user")
            sys.exit(0)
        return
    
    # Handle stealth mode
    if args.mode == "stealth":
        if args.exe is None and args.positional_exe is not None:
            args.exe = args.positional_exe
        if args.exe is None:
            raise SystemExit("Stealth mode requires --exe (or a positional exe path)")
        
        _configure_pyautogui()
        output_dir = args.output or args.screenshots
        
        config = AutomationConfig(
            exe_path=args.exe,
            window_title=args.window_title,
            screenshot_dir=output_dir,
            launch_wait=args.launch_wait,
            window_timeout=args.window_timeout,
            exit_timeout=args.exit_timeout,
            pointer_duration=args.pointer_duration,
            capture_delay=args.capture_delay,
        )
        
        try:
            runner = AutomationRunner(config)
            runner.run_stealth(delta_ms=args.delta, length_ms=args.length)
        except KeyboardInterrupt:
            logging.info("Stealth capture interrupted by user")
            sys.exit(0)
        return
    
    # Handle script mode (default)
    if args.script is None:
        raise SystemExit("Script mode requires --script pointing to the event transcript")
    if args.exe is None:
        raise SystemExit("Script mode requires --exe pointing to the target executable")
    
    _configure_pyautogui()
    
    if not args.script.exists():
        raise FileNotFoundError(f"Script not found: {args.script}")
    
    try:
        # Parse events
        parser = ScriptParser()
        events = parser.parse(args.script.read_text(encoding="utf-8").splitlines())
        
        if not events:
            raise SystemExit("No events to replay; script is empty")
        
        logging.info("Parsed %d events", len(events))
        
        # Run automation
        output_dir = args.output or args.screenshots
        
        config = AutomationConfig(
            exe_path=args.exe,
            window_title=args.window_title,
            screenshot_dir=output_dir,
            launch_wait=args.launch_wait,
            window_timeout=args.window_timeout,
            exit_timeout=args.exit_timeout,
            pointer_duration=args.pointer_duration,
            capture_delay=args.capture_delay,
        )
        
        runner = AutomationRunner(config)
        runner.run(events)
        
    except KeyboardInterrupt:
        logging.info("Replay interrupted by user")
        sys.exit(0)


if __name__ == "__main__":
    main()
