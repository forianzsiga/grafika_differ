"""Automation runner that coordinates process execution and event replay."""

import sys
import subprocess
import time
import logging
import platform
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional

from .event_types import Event

# Platform detection
IS_WINDOWS = platform.system().lower() == "windows"
IS_LINUX = platform.system().lower() == "linux"


@dataclass
class AutomationConfig:
    """Configuration for automation runner."""
    
    exe_path: Path
    window_title: Optional[str]
    screenshot_dir: Path
    launch_wait: float
    window_timeout: float
    exit_timeout: float
    pointer_duration: float
    capture_delay: float


class AutomationRunner:
    """Coordinates process launch, input replay, and screenshots."""

    def __init__(self, config: AutomationConfig) -> None:
        """Initialize automation runner with configuration."""
        self.config = config
        self.config.screenshot_dir.mkdir(parents=True, exist_ok=True)
        self._capture_index = 0
        
        # Initialize platform-specific components
        if IS_LINUX:
            # Lazy import to avoid circular imports
            import sys
            sys.path.insert(0, str(Path(__file__).parent.parent))
            try:
                from platform.x11_automation import (
                    X11WindowManager, X11Input, X11Screenshot, 
                    X11ProcessManager, setup_linux_environment
                )
                if not setup_linux_environment():
                    raise RuntimeError("Linux/X11 environment not properly configured")
                self.window_manager = X11WindowManager()
                self.screenshot_handler = X11Screenshot()
                self.input_handler = X11Input()
                self.process_manager = X11ProcessManager()
            except ImportError as e:
                raise ImportError(
                    f"Missing Linux-specific dependencies: {e}"
                )
        else:
            # For Windows, we'll need to import pywinauto
            try:
                import pywinauto
                from pywinauto.findwindows import ElementNotFoundError
                from pywinauto.timings import TimeoutError as PyWinTimeoutError
                self._pywinauto = (pywinauto.Application, ElementNotFoundError, PyWinTimeoutError)
            except ImportError as exc:
                raise ImportError(
                    "Missing Windows-specific dependency. Install with 'pip install pywinauto'. Original error: %s" % exc
                )

    def run(self, events: Iterable[Event]) -> None:
        """Run automation with the given events."""
        if not self.config.exe_path.exists():
            raise FileNotFoundError(f"Executable not found: {self.config.exe_path}")
        logging.info("Launching %s", self.config.exe_path)
        
        # Launch the process
        process = subprocess.Popen(
            [str(self.config.exe_path)],
            cwd=str(self.config.exe_path.parent),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            preexec_fn=lambda: None if IS_LINUX else None
        )
        
        try:
            if IS_LINUX:
                window = self._wait_for_window_linux(process.pid)
            else:  # Windows
                window = self._wait_for_window_windows(process.pid)
                
            logging.info("Window ready: %s", window)
            time.sleep(self.config.launch_wait)
            self._sleep_before_capture()
            
            if IS_LINUX:
                self._capture_window_linux(window, self._next_capture_path("after_launch"))
            else:  # Windows
                self._capture_window_windows(window, self._next_capture_path("after_launch"))
                
            for event in events:
                if IS_LINUX:
                    self._handle_event_linux(window, event)
                else:  # Windows
                    self._handle_event_windows(window, event)
                    
            self._await_exit(process)
        finally:
            self._cleanup_process(process)

    def run_stealth(self, delta_ms: int, length_ms: int) -> None:
        """Launch the app and capture the window at a fixed interval."""
        if not self.config.exe_path.exists():
            raise FileNotFoundError(f"Executable not found: {self.config.exe_path}")
        logging.info("Launching %s (stealth)", self.config.exe_path)
        
        process = subprocess.Popen(
            [str(self.config.exe_path)],
            cwd=str(self.config.exe_path.parent),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            preexec_fn=lambda: None if IS_LINUX else None
        )
        
        try:
            if IS_LINUX:
                window = self._wait_for_window_linux(process.pid)
            else:  # Windows
                window = self._wait_for_window_windows(process.pid)
                
            logging.info("Window ready: %s", window)
            time.sleep(self.config.launch_wait)
            self._sleep_before_capture()
            
            if IS_LINUX:
                self._capture_window_linux(window, self._next_capture_path("after_launch"))
            else:  # Windows
                self._capture_window_windows(window, self._next_capture_path("after_launch"))

            start = time.time()
            end_time = start + max(0.0, length_ms / 1000.0)
            interval = max(1, int(delta_ms)) / 1000.0
            next_ts = start
            while True:
                now = time.time()
                if now >= end_time:
                    break
                if now < next_ts:
                    time.sleep(max(0.0, next_ts - now))
                self._sleep_before_capture()
                label = f"stealth_{int((time.time() - start)*1000):07d}ms"
                
                if IS_LINUX:
                    self._capture_window_linux(window, self._next_capture_path(label))
                else:  # Windows
                    self._capture_window_windows(window, self._next_capture_path(label))
                    
                next_ts += interval

            self._sleep_before_capture()
            if IS_LINUX:
                self._capture_window_linux(window, self._next_capture_path("after_stealth"))
            else:  # Windows
                self._capture_window_windows(window, self._next_capture_path("after_stealth"))
                
            self._await_exit(process)
        finally:
            self._cleanup_process(process)

    # Windows-specific methods
    def _wait_for_window_windows(self, pid: int):
        """Wait for window on Windows using pywinauto."""
        Application, ElementNotFoundError, PyWinTimeoutError = self._pywinauto
        deadline = time.time() + self.config.window_timeout
        app = Application(backend="uia")
        while time.time() < deadline:
            try:
                app.connect(process=pid)
                window = (
                    app.window(title=self.config.window_title)
                    if self.config.window_title
                    else app.top_window()
                )
                wrapper = window.wrapper_object()
                wrapper.set_focus()
                return wrapper
            except (ElementNotFoundError, PyWinTimeoutError):
                time.sleep(0.2)
            except Exception as exc:
                logging.debug("Window lookup retry due to: %s", exc)
                time.sleep(0.2)
        raise TimeoutError(f"Failed to locate window within {self.config.window_timeout} seconds")

    def _handle_event_windows(self, window, event: Event) -> None:
        """Handle event on Windows using pyautogui and pywinauto."""
        logging.info("Event %03d: %s", event.index, event.raw)
        if event.delta > 0:
            time.sleep(event.delta)
        if event.action == "mouse_press":
            self._send_mouse_windows(window, event, press=True)
        elif event.action == "mouse_release":
            self._send_mouse_windows(window, event, press=False)
        elif event.action == "key_press":
            self._send_key_windows(event)
        elif event.action == "key_release":
            logging.debug("Key release event: %s", event.raw)
        elif event.action == "exit":
            exit_path = self._event_screenshot_path(event)
            self._sleep_before_capture()
            self._capture_window_windows(window, exit_path)
            try:
                window.close()
            except Exception as exc:
                logging.debug("Window close via UI failed: %s", exc)
            return
        else:
            logging.warning("Unhandled event action: %s", event.action)
        screenshot_path = self._event_screenshot_path(event)
        self._sleep_before_capture()
        self._capture_window_windows(window, screenshot_path)

    def _send_mouse_windows(self, window, event: Event, press: bool) -> None:
        """Send mouse event on Windows using pyautogui."""
        import pyautogui
        coords = None
        if event.window_point:
            try:
                coords = window.client_to_screen(event.window_point)
            except Exception as exc:
                logging.warning("Falling back to absolute coords for %s: %s", event.raw, exc)
        if coords:
            if self.config.pointer_duration > 0:
                pyautogui.moveTo(coords[0], coords[1], duration=self.config.pointer_duration)
            else:
                pyautogui.moveTo(coords[0], coords[1])
        button = event.button or "left"
        if press:
            pyautogui.mouseDown(button=button)
        else:
            pyautogui.mouseUp(button=button)

    def _send_key_windows(self, event: Event) -> None:
        """Send keyboard event on Windows using pyautogui."""
        import pyautogui
        if event.button:
            key = event.button
            pyautogui.press(key)

    def _capture_window_windows(self, window, path: Path) -> None:
        """Capture window on Windows using pywinauto."""
        import pyautogui
        region = self._client_region_windows(window)
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
            self._capture_screen_windows(path)

    def _client_region_windows(self, window) -> Optional[tuple]:
        """Get client region for Windows window."""
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

    def _capture_screen_windows(self, path: Path) -> None:
        """Capture full screen on Windows."""
        import pyautogui
        logging.debug("Capturing screen to %s", path)
        image = pyautogui.screenshot()
        image.save(path)

    # Linux-specific methods
    def _wait_for_window_linux(self, pid: int):
        """Wait for window on Linux using X11 with improved detection."""
        deadline = time.time() + self.config.window_timeout
        while time.time() < deadline:
            try:
                window_id = None
                
                if self.config.window_title:
                    logging.debug(f"Searching for window with title containing: '{self.config.window_title}'")
                    window_id = self.window_manager.find_window_by_title(self.config.window_title)
                
                if not window_id:
                    logging.debug(f"Searching for windows by process ID: {pid}")
                    windows_by_process = self.window_manager.find_windows_by_process(pid)
                    if windows_by_process:
                        window_id = windows_by_process[0]
                        logging.debug(f"Found window 0x{window_id:x} by process {pid}")
                
                if not window_id and not self.config.window_title:
                    logging.debug("Searching for any visible window")
                    window_id = self.window_manager.find_any_visible_window()
                    if window_id:
                        logging.debug(f"Found fallback window 0x{window_id:x}")
                
                if window_id:
                    if self.window_manager.focus_window(window_id):
                        logging.info(f"Successfully focused window 0x{window_id:x}")
                        return window_id
                        
                time.sleep(0.2)
            except Exception as exc:
                logging.debug("Window lookup retry due to: %s", exc)
                time.sleep(0.2)
        raise TimeoutError(f"Failed to locate window within {self.config.window_timeout} seconds")

    def _handle_event_linux(self, window_id: int, event: Event) -> None:
        """Handle event on Linux using X11."""
        logging.info("Event %03d: %s", event.index, event.raw)
        if event.delta > 0:
            time.sleep(event.delta)
        if event.action == "mouse_press":
            self._send_mouse_linux(window_id, event, press=True)
        elif event.action == "mouse_release":
            self._send_mouse_linux(window_id, event, press=False)
        elif event.action == "key_press":
            self._send_key_linux(window_id, event)
        elif event.action == "key_release":
            logging.debug("Key release event: %s", event.raw)
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
            if self.config.pointer_duration > 0:
                self.input_handler.move_mouse(coords[0], coords[1], duration=self.config.pointer_duration)
            else:
                self.input_handler.move_mouse(coords[0], coords[1])
        
        button = event.button or "left"
        if press:
            self.input_handler.mouse_press(button)
        else:
            self.input_handler.mouse_release(button)

    def _send_key_linux(self, window_id: int, event: Event) -> None:
        """Send keyboard event on Linux using X11."""
        if event.button:
            key = event.button
            self.input_handler.send_key_to_window(window_id, key)

    def _capture_window_linux(self, window_id: int, path: Path) -> None:
        """Capture window on Linux using X11."""
        logging.debug("Capturing window %s to %s", window_id, path)
        success = self.screenshot_handler.capture_window(window_id, path)
        if not success:
            logging.warning("Window capture failed, falling back to full screen")
            self.screenshot_handler.capture_screen(path)

    # Common methods
    def _sleep_before_capture(self) -> None:
        """Sleep before capture if configured."""
        if self.config.capture_delay > 0:
            time.sleep(self.config.capture_delay)

    def _event_screenshot_path(self, event: Event) -> Path:
        """Generate screenshot path for an event."""
        import re
        safe_label = re.sub(r"[^A-Za-z0-9_]+", "_", event.label()).strip("_") or "event"
        millis = int(round(event.timestamp * 1000))
        label = f"{millis:07d}_{event.index:03d}_{safe_label}"
        return self._next_capture_path(label)

    def _next_capture_path(self, label: str) -> Path:
        """Generate next capture path."""
        filename = f"{self._capture_index:03d}_{label}.png"
        self._capture_index += 1
        return self.config.screenshot_dir / filename

    def _cleanup_process(self, process: subprocess.Popen) -> None:
        """Clean up process."""
        if process.poll() is None:
            logging.info("Terminating process %s", process.pid)
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                logging.info("Force killing hung process %s", process.pid)
                process.kill()

    def _await_exit(self, process: subprocess.Popen) -> None:
        """Wait for process exit."""
        if self.config.exit_timeout <= 0:
            return
        try:
            if IS_LINUX and hasattr(self, 'process_manager'):
                start_time = time.time()
                while time.time() - start_time < self.config.exit_timeout:
                    if not self.process_manager.is_process_running(process.pid):
                        return
                    time.sleep(0.1)
            else:
                process.wait(timeout=self.config.exit_timeout)
        except subprocess.TimeoutExpired:
            logging.warning("Process did not exit within %.1f seconds", self.config.exit_timeout)
