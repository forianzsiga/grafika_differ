"""
Platform-specific automation implementations.

This module provides cross-platform support through abstract interfaces
and platform-specific implementations for different operating systems.
"""

from .base import WindowManager, InputHandler, ScreenshotHandler, ProcessManager

__all__ = [
    'WindowManager', 'InputHandler', 'ScreenshotHandler', 'ProcessManager',
]
