"""Automation framework for replaying recorded mouse scripts against the GreenTriangle demo.

Cross-platform automation that works on both Windows and Linux/X11.

This script expects an input transcript of interaction events such as::

    [ +0.370s ] onMousePressed L: window(100,100) -> world(-16.666666,16.666666)
    [ +0.370s ] onMouseReleased L: window(100,100) -> world(-16.666666,16.666666)
    ...
    [ +4.370s ] Exiting application

It launches the target executable, waits for its main window to become ready, replays
mouse activity according to the timing information in the transcript, captures full-screen
screenshots between events, and stores a dedicated window capture when the application exits.

Required third-party packages (install with ``pip``):
    - pyautogui
    - pillow (pulled in automatically by pyautogui but listed for clarity)
    
Windows-specific:
    - pywinauto
    
Linux/X11-specific:
    - python-xlib
    - psutil
    - xdotool (recommended for better input handling)

Example usage::

    python automation_framework.py \
        --mode script \
        --script events.txt \
        --exe glProgram/x64/Debug/GreenTriangle.exe \
        --window-title "GreenTriangle" \
        --output screenshots/run01

    python automation_framework.py \
        --mode comparison \
        --inputs screenshots/run01 screenshots/run02 \
        --output screenshots/comparison01

    python automation_framework.py \
        --mode interactive \
        --inputs screenshots/run01 screenshots/run02 screenshots/comparison01

    python automation_framework.py \
        --mode stealth \
        --exe glProgram/x64/Debug/GreenTriangle.exe \
        --window-title "GreenTriangle" \
        --output screenshots/run02 \
        --capture-delay 0.05 \
        --delta 50 \
        --length 5000
"""

from __future__ import annotations

import argparse
import logging
import platform
import re
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional, Tuple

from PIL import Image, ImageChops
try:
    import tkinter as tk
    from PIL import ImageTk
except Exception:  # pragma: no cover - tkinter may be missing in some environments
    tk = None
    ImageTk = None

try:
    import pyautogui
    from PIL import Image
except ImportError as exc:
    missing = "pyautogui, pillow"
    raise SystemExit(
        "Missing required dependency. Install with 'pip install %s'. Original error: %s"
        % (missing, exc)
    )

# Platform detection
IS_WINDOWS = platform.system().lower() == "windows"
IS_LINUX = platform.system().lower() == "linux"

# Import platform-specific dependencies
if IS_WINDOWS:
    try:
        from pywinauto import Application
        from pywinauto.findwindows import ElementNotFoundError
        from pywinauto.timings import TimeoutError as PyWinTimeoutError
    except ImportError as exc:
        missing = "pywinauto"
        raise SystemExit(
            "Missing Windows-specific dependency. Install with 'pip install pywinauto'. Original error: %s" % exc
        )
elif IS_LINUX:
    try:
        from Xlib import X, display
        import psutil
        # Import our X11 automation module
        from x11_automation import X11WindowManager, X11Screenshot, X11Input, ProcessManager, setup_linux_environment
    except ImportError as exc:
        missing = "python-xlib, psutil"
        raise SystemExit(
            "Missing Linux-specific dependency. Install with 'pip install python-xlib psutil'. Original error: %s" % exc
        )


def _configure_pyautogui() -> None:
    """Applies fail-safe defaults for pyautogui before replay begins."""
    pyautogui.FAILSAFE = False
    pyautogui.PAUSE = 0.0


@dataclass
class Event:
    index: int
    timestamp: float
    delta: float
    action: str
    button: Optional[str]
    window_point: Optional[Tuple[int, int]]
    world_point: Optional[Tuple[float, float]]
    raw: str

    def label(self) -> str:
        base = self.action
        if self.button:
            base = f"{base}_{self.button}"
        return base


class ScriptParser:
    """Parses the textual transcript into structured events."""

    DELTA_RE = re.compile(r"\[\s*\+(?P<delta>\d+(?:\.\d+)?)s\s*\]\s*(?P<body>.+)$")
    MOUSE_RE = re.compile(
        r"onMouse(?P<state>Pressed|Released)\s+(?P<button>[LR]):\s*(?P<details>.+)",
        re.IGNORECASE,
    )
    WINDOW_RE = re.compile(
        r"window\((?P<x>-?\d+(?:\.\d+)?),(?P<y>-?\d+(?:\.\d+)?)\)",
        re.IGNORECASE,
    )
    WORLD_RE = re.compile(
        r"world\((?P<x>-?\d+(?:\.\d+)?),(?P<y>-?\d+(?:\.\d+)?)\)",
        re.IGNORECASE,
    )

    def parse(self, lines: Iterable[str]) -> List[Event]:
        events: List[Event] = []
        for idx, raw_line in enumerate(lines, start=1):
            line = raw_line.strip()
            if not line:
                continue
            events.append(self._parse_line(line, len(events)))
        self._assign_deltas(events)
        return events

    def _parse_line(self, line: str, event_index: int) -> Event:
        delta_match = self.DELTA_RE.match(line)
        if not delta_match:
            raise ValueError(f"Could not parse timestamp in line: {line}")
        timestamp = float(delta_match.group("delta"))
        body = delta_match.group("body")

        mouse_match = self.MOUSE_RE.match(body)
        if mouse_match:
            state = mouse_match.group("state").lower()
            button = mouse_match.group("button").upper()
            details = mouse_match.group("details")
            window_point = self._parse_window(details)
            world_point = self._parse_world(details)
            action = "mouse_press" if state == "pressed" else "mouse_release"
            button_name = "left" if button == "L" else "right"
            if button not in {"L", "R"}:
                raise ValueError(f"Unsupported mouse button in line: {line}")
            return Event(
                index=event_index,
                timestamp=timestamp,
                delta=0.0,
                action=action,
                button=button_name,
                window_point=window_point,
                world_point=world_point,
                raw=line,
            )

        if "exiting application" in body.lower():
            return Event(
                index=event_index,
                timestamp=timestamp,
                delta=0.0,
                action="exit",
                button=None,
                window_point=None,
                world_point=None,
                raw=line,
            )

        raise ValueError(f"Unsupported event line: {line}")

    def _parse_window(self, details: str) -> Optional[Tuple[int, int]]:
        match = self.WINDOW_RE.search(details)
        if not match:
            return None
        x = int(round(float(match.group("x"))))
        y = int(round(float(match.group("y"))))
        return x, y

    def _parse_world(self, details: str) -> Optional[Tuple[float, float]]:
        match = self.WORLD_RE.search(details)
        if not match:
            return None
        x = float(match.group("x"))
        y = float(match.group("y"))
        return x, y

    def _assign_deltas(self, events: List[Event]) -> None:
        if not events:
            return
        prev_timestamp = 0.0
        for event in events:
            delta = event.timestamp - prev_timestamp
            if delta < 0:
                logging.debug(
                    "Non-monotonic timestamp detected (%.3f -> %.3f); clamping to 0",
                    prev_timestamp,
                    event.timestamp,
                )
                delta = 0.0
            event.delta = delta
            prev_timestamp = max(prev_timestamp, event.timestamp)


class AutomationRunner:
    """Coordinates process launch, input replay, and screenshots."""

    def __init__(
        self,
        exe_path: Path,
        window_title: Optional[str],
        screenshot_dir: Path,
        launch_wait: float,
        window_timeout: float,
        exit_timeout: float,
        pointer_duration: float,
        capture_delay: float,
    ) -> None:
        self.exe_path = exe_path
        self.window_title = window_title
        self.screenshot_dir = screenshot_dir
        self.launch_wait = launch_wait
        self.window_timeout = window_timeout
        self.exit_timeout = exit_timeout
        self.pointer_duration = pointer_duration
        self.capture_delay = capture_delay
        self.screenshot_dir.mkdir(parents=True, exist_ok=True)
        self._capture_index = 0
        
        # Initialize platform-specific components
        if IS_WINDOWS:
            self.window_manager = None  # Will be created per window
        elif IS_LINUX:
            # Setup Linux environment
            if not setup_linux_environment():
                raise RuntimeError("Linux/X11 environment not properly configured")
            self.window_manager = X11WindowManager()
            self.screenshot_handler = X11Screenshot()
            self.input_handler = X11Input()
            self.process_manager = ProcessManager()

    def run(self, events: Iterable[Event]) -> None:
        if not self.exe_path.exists():
            raise FileNotFoundError(f"Executable not found: {self.exe_path}")
        logging.info("Launching %s", self.exe_path)
        
        # Launch the process
        if IS_WINDOWS:
            process = subprocess.Popen(
                [str(self.exe_path)],
                cwd=str(self.exe_path.parent),
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        else:  # Linux
            process = subprocess.Popen(
                [str(self.exe_path)],
                cwd=str(self.exe_path.parent),
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                preexec_fn=lambda: None  # Ensure process doesn't inherit X11 session
            )
        
        try:
            if IS_WINDOWS:
                window = self._wait_for_window(process.pid)
            else:  # Linux
                window = self._wait_for_window_linux(process.pid)
                
            logging.info("Window ready: %s", window)
            time.sleep(self.launch_wait)
            self._sleep_before_capture()
            
            if IS_WINDOWS:
                self._capture_window(window, self._next_capture_path("after_launch"))
            else:  # Linux
                self._capture_window_linux(window, self._next_capture_path("after_launch"))
                
            for event in events:
                if IS_WINDOWS:
                    self._handle_event(window, event)
                else:  # Linux
                    self._handle_event_linux(window, event)
                    
            self._await_exit(process)
        finally:
            self._cleanup_process(process)

    def run_stealth(self, delta_ms: int, length_ms: int) -> None:
        """Launch the app and capture the window at a fixed interval for the given duration.

        No input events are injected. Frames are captured every ``delta_ms`` milliseconds
        for a total of ``length_ms`` milliseconds. An initial frame is captured after launch.
        """
        if not self.exe_path.exists():
            raise FileNotFoundError(f"Executable not found: {self.exe_path}")
        logging.info("Launching %s (stealth)", self.exe_path)
        
        # Launch the process
        if IS_WINDOWS:
            process = subprocess.Popen(
                [str(self.exe_path)],
                cwd=str(self.exe_path.parent),
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        else:  # Linux
            process = subprocess.Popen(
                [str(self.exe_path)],
                cwd=str(self.exe_path.parent),
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                preexec_fn=lambda: None
            )
        
        try:
            if IS_WINDOWS:
                window = self._wait_for_window(process.pid)
            else:  # Linux
                window = self._wait_for_window_linux(process.pid)
                
            logging.info("Window ready: %s", window)
            time.sleep(self.launch_wait)
            self._sleep_before_capture()
            
            if IS_WINDOWS:
                self._capture_window(window, self._next_capture_path("after_launch"))
            else:  # Linux
                self._capture_window_linux(window, self._next_capture_path("after_launch"))

            start = time.time()
            end_time = start + max(0.0, length_ms / 1000.0)
            interval = max(1, int(delta_ms)) / 1000.0
            next_ts = start
            while True:
                now = time.time()
                if now >= end_time:
                    break
                # sleep until next tick
                if now < next_ts:
                    time.sleep(max(0.0, next_ts - now))
                self._sleep_before_capture()
                label = f"stealth_{int((time.time() - start)*1000):07d}ms"
                
                if IS_WINDOWS:
                    self._capture_window(window, self._next_capture_path(label))
                else:  # Linux
                    self._capture_window_linux(window, self._next_capture_path(label))
                    
                next_ts += interval

            # capture a final frame at end
            self._sleep_before_capture()
            if IS_WINDOWS:
                self._capture_window(window, self._next_capture_path("after_stealth"))
            else:  # Linux
                self._capture_window_linux(window, self._next_capture_path("after_stealth"))
                
            self._await_exit(process)
        finally:
            self._cleanup_process(process)

    def _wait_for_window(self, pid: int):
        deadline = time.time() + self.window_timeout
        app = Application(backend="uia")
        while time.time() < deadline:
            try:
                app.connect(process=pid)
                window = (
                    app.window(title=self.window_title)
                    if self.window_title
                    else app.top_window()
                )
                wrapper = window.wrapper_object()
                wrapper.set_focus()
                return wrapper
            except (ElementNotFoundError, PyWinTimeoutError):
                time.sleep(0.2)
            except Exception as exc:  # pragma: no cover - defensive logging
                logging.debug("Window lookup retry due to: %s", exc)
                time.sleep(0.2)
        raise TimeoutError(f"Failed to locate window within {self.window_timeout} seconds")

    def _handle_event(self, window, event: Event) -> None:
        logging.info("Event %03d: %s", event.index, event.raw)
        if event.delta > 0:
            time.sleep(event.delta)
        if event.action == "mouse_press":
            self._send_mouse(window, event, press=True)
        elif event.action == "mouse_release":
            self._send_mouse(window, event, press=False)
        elif event.action == "exit":
            exit_path = self._event_screenshot_path(event)
            self._sleep_before_capture()
            self._capture_window(window, exit_path)
            try:
                window.close()
            except Exception as exc:
                logging.debug("Window close via UI failed: %s", exc)
            return
            return
        else:
            logging.warning("Unhandled event action: %s", event.action)
        screenshot_path = self._event_screenshot_path(event)
        self._sleep_before_capture()
        self._capture_window(window, screenshot_path)

    def _send_mouse(self, window, event: Event, press: bool) -> None:
        coords = None
        if event.window_point:
            try:
                coords = window.client_to_screen(event.window_point)
            except Exception as exc:
                logging.warning("Falling back to absolute coords for %s: %s", event.raw, exc)
        if coords:
            if self.pointer_duration > 0:
                pyautogui.moveTo(coords[0], coords[1], duration=self.pointer_duration)
            else:
                pyautogui.moveTo(coords[0], coords[1])
        button = event.button or "left"
        if press:
            pyautogui.mouseDown(button=button)
        else:
            pyautogui.mouseUp(button=button)

    def _capture_screen(self, path: Path) -> None:
        logging.debug("Capturing screen to %s", path)
        image = pyautogui.screenshot()
        image.save(path)

    def _capture_window(self, window, path: Path) -> None:
        region = self._client_region(window)
        if region:
            try:
                image = pyautogui.screenshot(region=region)
                image.save(path)
                return
            except Exception as exc:
                logging.warning("Client-area capture failed (%s); retrying with full window", exc)
        try:
            image = window.capture_as_image()
            image.save(path)
        except Exception as exc:
            logging.warning("Window capture failed (%s), falling back to full screen", exc)
            self._capture_screen(path)

    def _sleep_before_capture(self) -> None:
        if self.capture_delay > 0:
            time.sleep(self.capture_delay)

    def _event_screenshot_path(self, event: Event) -> Path:
        safe_label = re.sub(r"[^A-Za-z0-9_]+", "_", event.label()).strip("_") or "event"
        millis = int(round(event.timestamp * 1000))
        label = f"{millis:07d}_{event.index:03d}_{safe_label}"
        return self._next_capture_path(label)

    def _next_capture_path(self, label: str) -> Path:
        filename = f"{self._capture_index:03d}_{label}.png"
        self._capture_index += 1
        return self.screenshot_dir / filename

    def _client_region(self, window) -> Optional[Tuple[int, int, int, int]]:
        try:
            rect = window.client_rect()
            left, top = int(rect.left), int(rect.top)
            width = int(rect.width())
            height = int(rect.height())
            if width <= 0 or height <= 0:
                raise ValueError("Invalid client rectangle size")
            return left, top, width, height
        except Exception as exc:
            logging.debug("Unable to obtain client region: %s", exc)
            return None

    def _cleanup_process(self, process: subprocess.Popen) -> None:
        if process.poll() is None:
            logging.info("Terminating process %s", process.pid)
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                logging.info("Force killing hung process %s", process.pid)
                process.kill()

    # Linux-specific methods
    def _wait_for_window_linux(self, pid: int):
        """Wait for window on Linux using X11."""
        deadline = time.time() + self.window_timeout
        while time.time() < deadline:
            try:
                # Try to find window by title or by process
                if self.window_title:
                    window_id = self.window_manager.find_window_by_title(self.window_title)
                else:
                    # Find any window created by this process
                    window_id = self._find_window_by_process_linux(pid)
                
                if window_id:
                    # Focus the window
                    if self.window_manager.focus_window(window_id):
                        return window_id
                        
                time.sleep(0.2)
            except Exception as exc:
                logging.debug("Window lookup retry due to: %s", exc)
                time.sleep(0.2)
        raise TimeoutError(f"Failed to locate window within {self.window_timeout} seconds")

    def _find_window_by_process_linux(self, pid: int) -> Optional[int]:
        """Find window by process ID on Linux."""
        try:
            # Try to find window by looking for windows created by the process
            windows = self.window_manager._get_window_tree()
            for window_id, window_info in windows.items():
                # This is a simplified approach - in practice, you might need
                # to track window creation from the process
                if self.window_title and window_info.get('name'):
                    if self.window_title.lower() in window_info['name'].lower():
                        return window_id
        except Exception as e:
            logging.debug(f"Error finding window by process {pid}: {e}")
        return None

    def _handle_event_linux(self, window_id: int, event: Event) -> None:
        """Handle event on Linux using X11."""
        logging.info("Event %03d: %s", event.index, event.raw)
        if event.delta > 0:
            time.sleep(event.delta)
        if event.action == "mouse_press":
            self._send_mouse_linux(window_id, event, press=True)
        elif event.action == "mouse_release":
            self._send_mouse_linux(window_id, event, press=False)
        elif event.action == "exit":
            exit_path = self._event_screenshot_path(event)
            self._sleep_before_capture()
            self._capture_window_linux(window_id, exit_path)
            try:
                self.window_manager.close_window(window_id)
            except Exception as exc:
                logging.debug("Window close via X11 failed: %s", exc)
            return
        else:
            logging.warning("Unhandled event action: %s", event.action)
        screenshot_path = self._event_screenshot_path(event)
        self._sleep_before_capture()
        self._capture_window_linux(window_id, screenshot_path)

    def _send_mouse_linux(self, window_id: int, event: Event, press: bool) -> None:
        """Send mouse event on Linux using X11."""
        coords = None
        if event.window_point:
            coords = event.window_point
        if coords:
            if self.pointer_duration > 0:
                self.input_handler.move_mouse(coords[0], coords[1], duration=self.pointer_duration)
            else:
                self.input_handler.move_mouse(coords[0], coords[1])
        
        button = event.button or "left"
        if press:
            self.input_handler.mouse_press(button)
        else:
            self.input_handler.mouse_release(button)

    def _capture_window_linux(self, window_id: int, path: Path) -> None:
        """Capture window on Linux using X11."""
        logging.debug("Capturing window %s to %s", window_id, path)
        success = self.screenshot_handler.capture_window(window_id, path)
        if not success:
            logging.warning("Window capture failed, falling back to full screen")
            self.screenshot_handler.capture_screen(path)

    def _await_exit(self, process: subprocess.Popen) -> None:
        """Wait for process exit (cross-platform)."""
        if self.exit_timeout <= 0:
            return
        try:
            if IS_WINDOWS:
                process.wait(timeout=self.exit_timeout)
            else:  # Linux
                if hasattr(self, 'process_manager'):
                    # Use psutil for more reliable process checking on Linux
                    start_time = time.time()
                    while time.time() - start_time < self.exit_timeout:
                        if not self.process_manager.is_process_running(process.pid):
                            return
                        time.sleep(0.1)
                    logging.warning("Process did not exit within %.1f seconds", self.exit_timeout)
                else:
                    process.wait(timeout=self.exit_timeout)
        except subprocess.TimeoutExpired:
            logging.warning("Process did not exit within %.1f seconds", self.exit_timeout)


def _run_comparison(inputs: List[Path], output_dir: Path) -> None:
    """Generates absolute pixel-wise diffs between matching frames in two runs."""
    if len(inputs) != 2:
        raise ValueError("Comparison mode expects exactly two input directories")
    first_dir, second_dir = inputs
    for directory in (first_dir, second_dir):
        if not directory.exists() or not directory.is_dir():
            raise FileNotFoundError(f"Input directory not found: {directory}")
    output_dir.mkdir(parents=True, exist_ok=True)

    first_files = {path.name: path for path in first_dir.glob("*.png")}
    second_files = {path.name: path for path in second_dir.glob("*.png")}
    shared_names = sorted(first_files.keys() & second_files.keys())
    if not shared_names:
        raise SystemExit("No matching frames to compare; ensure filenames align")

    unmatched_first = sorted(first_files.keys() - second_files.keys())
    unmatched_second = sorted(second_files.keys() - first_files.keys())
    for name in unmatched_first:
        logging.warning("Skipping frame present only in first input: %s", name)
    for name in unmatched_second:
        logging.warning("Skipping frame present only in second input: %s", name)

    processed = 0
    for name in shared_names:
        out_name = Path(name).stem + "_diff" + Path(name).suffix
        output_path = output_dir / out_name
        with Image.open(first_files[name]) as img_a, Image.open(second_files[name]) as img_b:
            if img_a.size != img_b.size:
                logging.warning(
                    "Skipping %s due to size mismatch (%s vs %s)",
                    name,
                    img_a.size,
                    img_b.size,
                )
                continue
            if img_a.mode != img_b.mode:
                img_b = img_b.convert(img_a.mode)
            diff = ImageChops.difference(img_a, img_b)
            diff.save(output_path)
            logging.info("Wrote diff frame: %s", output_path)
            processed += 1
    logging.info("Completed diff generation for %d frame(s)", processed)


def _run_interactive(inputs: List[Path]) -> None:
    """Launch a simple image viewer to flip through A/B/(optional diff) frames.

    Keyboard:
      Left/Right  - previous/next frame
      1           - side-by-side
      2           - overlay (alpha)
      3           - split (drag or , . to adjust)
      4           - diff (uses provided diff dir or computes on the fly)
      [ / ]       - decrease/increase overlay alpha
      , / .       - move split left/right
      F           - toggle fit-to-window
      H or ?      - toggle help overlay
    """
    if tk is None or ImageTk is None:
        raise SystemExit("Interactive mode requires tkinter and Pillow's ImageTk available in this environment")

    if len(inputs) < 2:
        raise SystemExit("Interactive mode requires at least two input directories (runA runB [diffDir])")

    dir_a, dir_b = inputs[0], inputs[1]
    dir_diff = inputs[2] if len(inputs) >= 3 else None
    for directory in (dir_a, dir_b) + (() if dir_diff is None else (dir_diff,)):
        if not directory.exists() or not directory.is_dir():
            raise FileNotFoundError(f"Input directory not found: {directory}")

    files_a = {p.name: p for p in dir_a.glob("*.png")}
    files_b = {p.name: p for p in dir_b.glob("*.png")}
    names = sorted(files_a.keys() & files_b.keys())
    if not names:
        raise SystemExit("No matching PNG filenames across the first two inputs")
    files_diff = {p.name: p for p in dir_diff.glob("*.png")} if dir_diff else {}

    class Viewer:
        def __init__(self):
            self.root = tk.Tk()
            self.root.title("Interactive Viewer")
            self.mode = 0  # 0 side, 1 overlay, 2 split, 3 diff
            self.modes = ["side-by-side", "overlay", "split", "diff"]
            self.index = 0
            self.alpha = 0.5
            self.split = 0.5
            self.fit = True
            self.help_on = True
            sw = self.root.winfo_screenwidth()
            sh = self.root.winfo_screenheight()
            self.canvas = tk.Canvas(self.root, width=min(1600, sw-100), height=min(900, sh-100), bg="#222")
            self.canvas.pack(fill=tk.BOTH, expand=True)
            self.canvas.bind("<Configure>", lambda e: self.render())
            self.canvas.bind("<Button-1>", self._on_click)
            self.canvas.bind("<B1-Motion>", self._on_drag)
            self.root.bind("<Left>", lambda e: self.prev())
            self.root.bind("<Right>", lambda e: self.next())
            self.root.bind("1", lambda e: self.set_mode(0))
            self.root.bind("2", lambda e: self.set_mode(1))
            self.root.bind("3", lambda e: self.set_mode(2))
            self.root.bind("4", lambda e: self.set_mode(3))
            self.root.bind("[", lambda e: self._set_alpha(self.alpha - 0.05))
            self.root.bind("]", lambda e: self._set_alpha(self.alpha + 0.05))
            self.root.bind(",", lambda e: self._set_split(self.split - 0.05))
            self.root.bind(".", lambda e: self._set_split(self.split + 0.05))
            self.root.bind("f", lambda e: self._toggle_fit())
            self.root.bind("F", lambda e: self._toggle_fit())
            self.root.bind("h", lambda e: self._toggle_help())
            self.root.bind("?", lambda e: self._toggle_help())
            self.photo = None
            self.render()

        def _toggle_fit(self):
            self.fit = not self.fit
            self.render()

        def _toggle_help(self):
            self.help_on = not self.help_on
            self.render()

        def set_mode(self, m):
            self.mode = m
            # change cursor when in split mode for visual affordance
            if self.mode == 2:
                try:
                    self.canvas.config(cursor="sb_h_double_arrow")
                except Exception:
                    self.canvas.config(cursor="")
            else:
                self.canvas.config(cursor="")
            self.render()

        def _set_alpha(self, a):
            self.alpha = max(0.0, min(1.0, a))
            if self.mode == 1:
                self.render()

        def _set_split(self, s):
            self.split = max(0.0, min(1.0, s))
            if self.mode == 2:
                self.render()

        def prev(self):
            self.index = (self.index - 1) % len(names)
            self.render()

        def next(self):
            self.index = (self.index + 1) % len(names)
            self.render()

        def _load_pair(self):
            name = names[self.index]
            a = Image.open(files_a[name]).convert("RGB")
            b = Image.open(files_b[name]).convert("RGB")
            if a.size != b.size:
                b = b.resize(a.size, Image.LANCZOS)
            d = None
            if name in files_diff:
                try:
                    d = Image.open(files_diff[name]).convert("RGB")
                    if d.size != a.size:
                        d = d.resize(a.size, Image.LANCZOS)
                except Exception:
                    d = None
            return name, a, b, d

        def _compose(self, a: Image.Image, b: Image.Image, d: Optional[Image.Image]) -> Image.Image:
            if self.mode == 0:  # side-by-side
                w, h = a.size
                out = Image.new("RGB", (w*2, h), (0, 0, 0))
                out.paste(a, (0, 0))
                out.paste(b, (w, 0))
                return out
            elif self.mode == 1:  # overlay
                return Image.blend(a, b, self.alpha)
            elif self.mode == 2:  # split
                w, h = a.size
                x = int(self.split * w)
                out = Image.new("RGB", (w, h), (0, 0, 0))
                out.paste(a.crop((0, 0, x, h)), (0, 0))
                out.paste(b.crop((x, 0, w, h)), (x, 0))
                return out
            else:  # diff
                if d is not None:
                    return d
                return ImageChops.difference(a, b)

        def _fit_image(self, img: Image.Image) -> Image.Image:
            cw = self.canvas.winfo_width()
            ch = self.canvas.winfo_height()
            if cw <= 1 or ch <= 1:
                return img
            if not self.fit:
                return img
            iw, ih = img.size
            scale = min(cw / iw, ch / ih)
            if scale < 1.0:
                nw, nh = max(1, int(iw * scale)), max(1, int(ih * scale))
                return img.resize((nw, nh), Image.LANCZOS)
            return img

        def render(self):
            name, a, b, d = self._load_pair()
            composed = self._compose(a, b, d)
            disp = self._fit_image(composed)
            self.photo = ImageTk.PhotoImage(disp)
            self.canvas.delete("all")
            cw = self.canvas.winfo_width()
            ch = self.canvas.winfo_height()
            x = max(0, (cw - disp.size[0]) // 2)
            y = max(0, (ch - disp.size[1]) // 2)
            # store drawn image geometry for hit testing / split mapping
            self._draw_x, self._draw_y = x, y
            self._draw_w, self._draw_h = disp.size
            self.canvas.create_image(x, y, anchor=tk.NW, image=self.photo)
            # draw visible splitter in split mode
            if self.mode == 2:
                sx = x + int(self.split * self._draw_w)
                self.canvas.create_line(sx, y, sx, y + self._draw_h, fill="#FFD54F", width=2)
            self.root.title(f"{names[self.index]}  |  {self.modes[self.mode]}  |  {dir_a.name} vs {dir_b.name}")
            if self.help_on:
                help_text = (
                    "←/→ prev/next   1 side  2 overlay  3 split  4 diff   "
                    "[/] alpha   ,/. split   F fit   H help"
                )
                self.canvas.create_text(10, 10, anchor=tk.NW, text=help_text, fill="#fff", font=("Segoe UI", 10))

        def _on_click(self, event):
            if self.mode == 2 and self.canvas.winfo_width() > 0:
                self._update_split_from_x(event.x)

        def _on_drag(self, event):
            if self.mode == 2 and self.canvas.winfo_width() > 0:
                self._update_split_from_x(event.x)

        def _update_split_from_x(self, x):
            # map canvas x to image-local x if image is centered
            draw_x = getattr(self, "_draw_x", 0)
            draw_w = max(1, getattr(self, "_draw_w", self.canvas.winfo_width()))
            rel = (x - draw_x) / draw_w
            self._set_split(rel)

    Viewer().root.mainloop()


def _parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Replay recorded UI script against an executable.")
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
    # Optional positional exe path primarily for convenience in stealth mode
    parser.add_argument("positional_exe", nargs="?", type=Path, help=argparse.SUPPRESS)
    parser.add_argument("--window-title", dest="window_title", help="Exact window title to focus; defaults to top window")
    parser.add_argument(
        "--screenshots",
        type=Path,
        default=Path("screenshots"),
        help="Directory where screenshots will be stored",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Directory where mode-specific outputs will be written",
    )
    parser.add_argument(
        "--inputs",
        nargs="+",
        type=Path,
        help="Input directories: 2 for comparison/interactive (optional 3rd is diff dir for interactive)",
    )
    parser.add_argument(
        "--launch-wait",
        type=float,
        default=1.5,
        help="Extra seconds to wait after the window becomes ready before replay",
    )
    parser.add_argument(
        "--window-timeout",
        type=float,
        default=15.0,
        help="Seconds to wait for the main window to appear",
    )
    parser.add_argument(
        "--exit-timeout",
        type=float,
        default=10.0,
        help="Seconds to wait for the process to exit after replay",
    )
    parser.add_argument(
        "--pointer-duration",
        type=float,
        default=0.0,
        help="Optional duration in seconds for mouse move animations",
    )
    parser.add_argument(
        "--capture-delay",
        type=float,
        default=0.0,
        help="Extra delay in seconds before each screenshot to let frames settle",
    )
    parser.add_argument(
        "--delta",
        type=int,
        default=50,
        help="Stealth mode: capture interval in milliseconds",
    )
    parser.add_argument(
        "--length",
        type=int,
        default=5000,
        help="Stealth mode: total capture duration in milliseconds",
    )
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Console log verbosity",
    )
    return parser.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> None:
    args = _parse_args(argv)
    logging.basicConfig(level=getattr(logging, args.log_level), format="%(asctime)s %(levelname)s %(message)s")
    if args.mode == "interactive":
        if not args.inputs or len(args.inputs) < 2:
            raise SystemExit("Interactive mode requires --inputs with 2 (optionally 3) directories")
        _run_interactive(list(args.inputs))
        return
    if args.mode == "comparison":
        if not args.inputs:
            raise SystemExit("Comparison mode requires exactly two --inputs directories")
        if args.output is None:
            raise SystemExit("Comparison mode requires an --output directory")
        _run_comparison(list(args.inputs), args.output)
        return

    # Allow positional exe path as a convenience (especially for stealth example)
    if args.exe is None and getattr(args, "positional_exe", None) is not None:
        args.exe = args.positional_exe

    if args.mode == "stealth":
        if args.exe is None:
            raise SystemExit("Stealth mode requires --exe (or a positional exe path) pointing to the target executable")
        _configure_pyautogui()
        output_dir = args.output or args.screenshots
        runner = AutomationRunner(
            exe_path=args.exe,
            window_title=args.window_title,
            screenshot_dir=output_dir,
            launch_wait=args.launch_wait,
            window_timeout=args.window_timeout,
            exit_timeout=args.exit_timeout,
            pointer_duration=args.pointer_duration,
            capture_delay=args.capture_delay,
        )
        runner.run_stealth(delta_ms=args.delta, length_ms=args.length)
        return

    if args.script is None:
        raise SystemExit("Script mode requires --script pointing to the event transcript")
    if args.exe is None:
        raise SystemExit("Script mode requires --exe pointing to the target executable")

    _configure_pyautogui()

    if not args.script.exists():
        raise FileNotFoundError(f"Script not found: {args.script}")

    parser = ScriptParser()
    events = parser.parse(args.script.read_text(encoding="utf-8").splitlines())
    if not events:
        raise SystemExit("No events to replay; script is empty")
    logging.info("Parsed %d events", len(events))

    output_dir = args.output or args.screenshots

    runner = AutomationRunner(
        exe_path=args.exe,
        window_title=args.window_title,
        screenshot_dir=output_dir,
        launch_wait=args.launch_wait,
        window_timeout=args.window_timeout,
        exit_timeout=args.exit_timeout,
        pointer_duration=args.pointer_duration,
        capture_delay=args.capture_delay,
    )
    runner.run(events)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logging.info("Replay interrupted by user")
        sys.exit(1)