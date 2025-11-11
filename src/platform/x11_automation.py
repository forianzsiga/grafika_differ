"""Linux/X11 automation framework for replaying recorded mouse scripts.

This module extends the Windows automation framework to work with X11 on Linux.
It provides X11-specific implementations for window management, screenshot capture,
and input simulation.

Required third-party packages (install with ``pip``):
    - pyautogui
    - python-xlib
    - psutil
    - pillow
"""

import os
import sys
import time
import logging
import platform
from pathlib import Path
from typing import Optional, Tuple, List

# Check if we're on Linux
IS_LINUX = platform.system().lower() == "linux"

if IS_LINUX:
    try:
        from Xlib import X, display, XK
        from Xlib.ext import xtest
        import psutil
        import subprocess
        import re
    except ImportError as exc:
        raise SystemExit(
            "Missing Linux-specific dependencies. Install with 'pip install python-xlib psutil'. Original error: %s" % exc
        )

from PIL import Image


class X11WindowManager:
    """X11-specific window management using python-xlib."""
    
    def __init__(self):
        if not IS_LINUX:
            raise RuntimeError("X11WindowManager can only be used on Linux")
        self.display = display.Display()
        self.screen = self.display.screen()
        self.root = self.screen.root
        
    def find_window_by_title(self, title_pattern: str) -> Optional[object]:
        """Find window by title pattern using X11."""
        windows = self._get_window_tree()
        
        for window_id, window_info in windows.items():
            window_title = self._get_window_title(window_id)
            window_class = self._get_window_class(window_id)
            # Check both title and class for the pattern
            if window_title and title_pattern.lower() in window_title.lower():
                return window_id
            if window_class and title_pattern.lower() in window_class.lower():
                return window_id
        return None
    
    def find_windows_by_process(self, pid: int) -> List[int]:
        """Find all windows belonging to a specific process using xdotool."""
        try:
            # Use xdotool to search for windows by process ID
            result = subprocess.run(
                ['xdotool', 'search', '--pid', str(pid)],
                capture_output=True, text=True, check=False
            )
            if result.returncode == 0 and result.stdout.strip():
                window_ids = []
                for line in result.stdout.strip().split('\n'):
                    if line.strip():
                        try:
                            window_ids.append(int(line.strip()))
                        except ValueError:
                            continue
                return window_ids
        except Exception as e:
            logging.debug(f"Error finding windows by process {pid}: {e}")
        return []
    
    def find_any_visible_window(self) -> Optional[int]:
        """Find any visible window that might be our target."""
        windows = self._get_window_tree()
        
        # Try to find windows with meaningful properties
        for window_id, window_info in windows.items():
            window_title = self._get_window_title(window_id)
            window_class = self._get_window_class(window_id)
            
            # Skip windows without any identifying information
            if not window_title and not window_class:
                continue
                
            # Skip system windows (usually have no title or very generic titles)
            if window_title and any(sys_win in window_title.lower() for sys_win in 
                                   ['desktop', 'panel', 'taskbar', 'menu', 'system', 'root']):
                continue
                
            # Return the first reasonable window we find
            if window_title or window_class:
                logging.debug(f"Found candidate window 0x{window_id:x}: title='{window_title}', class='{window_class}'")
                return window_id
        return None
    
    def _get_window_tree(self) -> dict:
        """Get all windows in the X11 window tree."""
        windows = {}
        
        def traverse_tree(window, depth=0):
            if depth > 10:  # Prevent infinite recursion
                return
                
            try:
                window_id = window.id
                windows[window_id] = {
                    'name': self._get_window_title(window_id),
                    'class': self._get_window_class(window_id),
                    'depth': depth
                }
                
                # Traverse children
                children = window.query_tree().children
                for child in children:
                    traverse_tree(child, depth + 1)
            except Exception as e:
                logging.debug(f"Error traversing window tree: {e}")
        
        traverse_tree(self.root)
        return windows
    
    def _get_window_title(self, window_id: int) -> Optional[str]:
        """Get window title using X11."""
        try:
            window = self.display.create_resource_object('window', window_id)
            title_prop = window.get_full_text_property(
                self.display.intern_atom('_NET_WM_NAME')
            )
            if title_prop:
                return title_prop.value
                
            # Fallback to older property
            title_prop = window.get_full_text_property(
                self.display.intern_atom('WM_NAME')
            )
            if title_prop:
                return title_prop.value
        except Exception as e:
            logging.debug(f"Error getting window title for {window_id}: {e}")
        return None
    
    def _get_window_class(self, window_id: int) -> Optional[str]:
        """Get window class using X11."""
        try:
            window = self.display.create_resource_object('window', window_id)
            class_prop = window.get_full_text_property(
                self.display.intern_atom('WM_CLASS')
            )
            if class_prop:
                return class_prop.value
        except Exception as e:
            logging.debug(f"Error getting window class for {window_id}: {e}")
        return None
    
    def get_window_geometry(self, window_id: int) -> Optional[Tuple[int, int, int, int]]:
        """Get window geometry (x, y, width, height)."""
        try:
            window = self.display.create_resource_object('window', window_id)
            geometry = window.get_geometry()
            return (geometry.x, geometry.y, geometry.width, geometry.height)
        except Exception as e:
            logging.debug(f"Error getting window geometry for {window_id}: {e}")
        return None
    
    def focus_window(self, window_id: int) -> bool:
        """Focus a window using X11."""
        try:
            window = self.display.create_resource_object('window', window_id)
            
            # Raise the window
            window.configure(stack_mode=X.Above)
            
            # Set input focus
            window.set_input_focus(X.RevertToParent, X.CurrentTime)
            
            self.display.sync()
            return True
        except Exception as e:
            logging.debug(f"Error focusing window {window_id}: {e}")
            return False
    
    def close_window(self, window_id: int) -> bool:
        """Close a window using X11."""
        try:
            window = self.display.create_resource_object('window', window_id)
            
            # Send WM_DELETE_WINDOW message
            wm_delete = self.display.intern_atom('WM_DELETE_WINDOW')
            window.event_send(X.Event(type=X.ClientMessage, 
                                    window=window_id,
                                    client_type=wm_delete,
                                    data=(32, [wm_delete, X.CurrentTime, 0, 0, 0])))
            
            self.display.sync()
            return True
        except Exception as e:
            logging.debug(f"Error closing window {window_id}: {e}")
            return False


class X11Screenshot:
    """X11-specific screenshot functionality."""
    
    def __init__(self):
        if not IS_LINUX:
            raise RuntimeError("X11Screenshot can only be used on Linux")
    
    def capture_window(self, window_id: int, output_path: Path) -> bool:
        """Capture a specific window using X11."""
        try:
            # Get window geometry
            wm = X11WindowManager()
            geometry = wm.get_window_geometry(window_id)
            if not geometry:
                logging.warning(f"Could not get geometry for window {window_id}")
                return False
            
            x, y, width, height = geometry
            
            # Use scrot for screenshot if available, otherwise use import
            try:
                # Try using scrot (usually more reliable)
                cmd = [
                    'scrot', '-z',  # -z to silent mode
                    '--focused',    # Capture focused window
                    str(output_path)
                ]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    logging.debug(f"Captured window using scrot: {output_path}")
                    return True
            except (subprocess.TimeoutExpired, FileNotFoundError):
                pass
            
            # Fallback to ImageMagick's import command
            try:
                cmd = [
                    'import',  # ImageMagick's import command
                    '-window', str(window_id),
                    str(output_path)
                ]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    logging.debug(f"Captured window using import: {output_path}")
                    return True
            except (subprocess.TimeoutExpired, FileNotFoundError):
                pass
            
            # Final fallback to xwd
            try:
                cmd = [
                    'xwd', '-id', str(window_id)
                ]
                with open(output_path.with_suffix('.xwd'), 'wb') as f:
                    result = subprocess.run(cmd, stdout=f, timeout=10)
                if result.returncode == 0:
                    # Convert xwd to png using convert
                    convert_cmd = ['convert', str(output_path.with_suffix('.xwd')), str(output_path)]
                    subprocess.run(convert_cmd, capture_output=True, timeout=10)
                    # Clean up xwd file
                    output_path.with_suffix('.xwd').unlink(missing_ok=True)
                    logging.debug(f"Captured window using xwd: {output_path}")
                    return True
            except (subprocess.TimeoutExpired, FileNotFoundError):
                pass
            
            logging.warning("No screenshot tool available. Install scrot, ImageMagick, or xwd.")
            return False
            
        except Exception as e:
            logging.error(f"Error capturing window {window_id}: {e}")
            return False
    
    def capture_screen(self, output_path: Path) -> bool:
        """Capture the entire screen using X11."""
        try:
            # Try scrot first
            try:
                cmd = ['scrot', str(output_path)]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    logging.debug(f"Captured screen using scrot: {output_path}")
                    return True
            except (subprocess.TimeoutExpired, FileNotFoundError):
                pass
            
            # Fallback to import
            try:
                cmd = ['import', str(output_path)]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    logging.debug(f"Captured screen using import: {output_path}")
                    return True
            except (subprocess.TimeoutExpired, FileNotFoundError):
                pass
            
            logging.warning("No screenshot tool available. Install scrot or ImageMagick.")
            return False
            
        except Exception as e:
            logging.error(f"Error capturing screen: {e}")
            return False


class X11Input:
    """X11-specific input simulation."""
    
    def __init__(self):
        if not IS_LINUX:
            raise RuntimeError("X11Input can only be used on Linux")
        self.display = display.Display()
    
    def move_mouse(self, x: int, y: int, duration: float = 0.0) -> bool:
        """Move mouse to coordinates using X11."""
        try:
            if duration > 0:
                # For smooth movement, we could implement interpolation here
                # For now, just move directly
                pass
            
            # Use xdotool if available for better reliability
            try:
                cmd = ['xdotool', 'mousemove', str(x), str(y)]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    return True
            except (subprocess.TimeoutExpired, FileNotFoundError):
                pass
            
            # Fallback to X11 direct input
            self.display.warp_pointer(None, self.display.screen().root, 0, 0, 0, 0, x, y)
            self.display.sync()
            return True
            
        except Exception as e:
            logging.error(f"Error moving mouse to ({x}, {y}): {e}")
            return False
    
    def mouse_press(self, button: str = "left") -> bool:
        """Press mouse button using X11."""
        try:
            button_code = self._get_button_code(button)
            if not button_code:
                return False
            
            # Try xdotool first
            try:
                cmd = ['xdotool', 'mousedown', str(button_code)]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    return True
            except (subprocess.TimeoutExpired, FileNotFoundError):
                pass
            
            # Fallback to X11 direct input
            event = X.ButtonPressEvent()
            event.window = self.display.screen().root
            event.root = self.display.screen().root
            event.subwindow = None
            event.time = X.CurrentTime
            event.x = 0
            event.y = 0
            event.x_root = 0
            event.y_root = 0
            event.state = 0
            event.button = button_code
            event.same_screen = 1
            
            self.display.send_event(event, self.display.screen().root, X.ButtonPressMask)
            self.display.sync()
            return True
            
        except Exception as e:
            logging.error(f"Error pressing mouse button {button}: {e}")
            return False
    
    def mouse_release(self, button: str = "left") -> bool:
        """Release mouse button using X11."""
        try:
            button_code = self._get_button_code(button)
            if not button_code:
                return False
            
            # Try xdotool first
            try:
                cmd = ['xdotool', 'mouseup', str(button_code)]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    return True
            except (subprocess.TimeoutExpired, FileNotFoundError):
                pass
            
            # Fallback to X11 direct input
            event = X.ButtonReleaseEvent()
            event.window = self.display.screen().root
            event.root = self.display.screen().root
            event.subwindow = None
            event.time = X.CurrentTime
            event.x = 0
            event.y = 0
            event.x_root = 0
            event.y_root = 0
            event.state = 0
            event.button = button_code
            event.same_screen = 1
            
            self.display.send_event(event, self.display.screen().root, X.ButtonReleaseMask)
            self.display.sync()
            return True
            
        except Exception as e:
            logging.error(f"Error releasing mouse button {button}: {e}")
            return False
    
    def _get_button_code(self, button: str) -> Optional[int]:
        """Get X11 button code for mouse button."""
        button_map = {
            "left": 1,
            "middle": 2,
            "right": 3,
            "4": 4,  # scroll up
            "5": 5,  # scroll down
            "6": 6,  # scroll left
            "7": 7   # scroll right
        }
        return button_map.get(button.lower())

    def send_key(self, key_sym_str: str) -> bool:
        """Send a key press and release using X11."""
        try:
            # Try xdotool first for better reliability
            try:
                cmd = ['xdotool', 'key', key_sym_str]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    return True
            except (subprocess.TimeoutExpired, FileNotFoundError):
                pass
            
            # Fallback to X11 direct input
            # Convert keysym to keycode
            keysym = XK.string_to_keysym(key_sym_str)
            if keysym == 0:
                logging.error(f"Unknown keysym: {key_sym_str}")
                return False
            keycode = self.display.keysym_to_keycode(keysym)
            if keycode == 0:
                logging.error(f"Could not resolve keycode for keysym {key_sym_str}")
                return False
            
            # Send press and release
            xtest.fake_input(self.display, X.KeyPress, keycode)
            self.display.sync()
            time.sleep(0.05)
            xtest.fake_input(self.display, X.KeyRelease, keycode)
            self.display.sync()
            return True
            
        except Exception as e:
            logging.error(f"Error sending key '{key_sym_str}': {e}")
            return False

    def send_key_to_window(self, window_id: int, key_sym_str: str) -> bool:
        """Send a key press and release to a specific window."""
        try:
            # Try to set input focus to the window
            try:
                window = self.display.create_resource_object('window', window_id)
                window.set_input_focus(X.RevertToParent, X.CurrentTime)
                self.display.sync()
                time.sleep(0.05)
            except Exception as e:
                logging.debug(f"Failed to set focus to window {window_id}: {e}")
            
            # Send the key using the send_key method
            return self.send_key(key_sym_str)
            
        except Exception as e:
            logging.error(f"Error sending key to window {window_id}: {e}")
            return False


class ProcessManager:
    """Cross-platform process management."""
    
    @staticmethod
    def find_process_by_name(process_name: str) -> Optional[int]:
        """Find process ID by name."""
        try:
            for proc in psutil.process_iter(['pid', 'name']):
                if process_name.lower() in proc.info['name'].lower():
                    return proc.info['pid']
        except Exception as e:
            logging.debug(f"Error finding process {process_name}: {e}")
        return None
    
    @staticmethod
    def is_process_running(pid: int) -> bool:
        """Check if process is running."""
        try:
            return psutil.pid_exists(pid)
        except Exception:
            return False
    
    @staticmethod
    def terminate_process(pid: int) -> bool:
        """Terminate a process gracefully."""
        try:
            proc = psutil.Process(pid)
            proc.terminate()
            return True
        except Exception as e:
            logging.debug(f"Error terminating process {pid}: {e}")
            return False
    
    @staticmethod
    def kill_process(pid: int) -> bool:
        """Force kill a process."""
        try:
            proc = psutil.Process(pid)
            proc.kill()
            return True
        except Exception as e:
            logging.debug(f"Error killing process {pid}: {e}")
            return False


def check_x11_dependencies() -> List[str]:
    """Check if required X11 tools are available."""
    missing = []
    
    # Check for screenshot tools
    screenshot_tools = ['scrot', 'import', 'xwd']
    found_screenshot = False
    for tool in screenshot_tools:
        if subprocess.run(['which', tool], capture_output=True).returncode == 0:
            found_screenshot = True
            break
    
    if not found_screenshot:
        missing.append("screenshot tool (install scrot, imagemagick, or xwd)")
    
    # Check for input tools
    if subprocess.run(['which', 'xdotool'], capture_output=True).returncode != 0:
        missing.append("xdotool")
    
    # Check for X11 display
    if not os.environ.get('DISPLAY'):
        missing.append("DISPLAY environment variable (X11 server not running)")
    
    return missing


def setup_linux_environment():
    """Setup and validate Linux/X11 environment."""
    if not IS_LINUX:
        logging.warning("Not running on Linux - X11 features will not be available")
        return False
    
    missing = check_x11_dependencies()
    if missing:
        logging.error("Missing required X11 dependencies:")
        for item in missing:
            logging.error(f"  - {item}")
        logging.error("Please install missing dependencies and ensure X11 is running")
        return False
    
    logging.info("Linux/X11 environment validated successfully")
    return True


if __name__ == "__main__":
    # Test X11 functionality
    if setup_linux_environment():
        print("X11 environment is ready")
        
        # Test window manager
        wm = X11WindowManager()
        print("Window manager initialized")
        
        # Test screenshot
        screenshot = X11Screenshot()
        print("Screenshot functionality ready")
        
        # Test input
        input_handler = X11Input()
        print("Input handler ready")
    else:
        print("X11 environment setup failed")