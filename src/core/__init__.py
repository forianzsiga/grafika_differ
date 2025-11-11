"""
Core automation framework components.

This module contains the heart of the automation system including
event definitions, parsing, and execution logic.
"""

from .event_types import Event
from .event_parser import ScriptParser
from .automation_runner import AutomationRunner, AutomationConfig

__all__ = ['Event', 'ScriptParser', 'AutomationRunner', 'AutomationConfig']
