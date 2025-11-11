"""Script parser for converting transcript text to structured events."""

import re
from typing import Iterable, List, Optional, Tuple
from .event_types import Event


class ScriptParser:
    """Parses the textual transcript into structured events."""

    DELTA_RE = re.compile(r"\[\s*\+(?P<delta>\d+(?:\.\d+)?)s\s*\]\s*(?P<body>.+)$")
    MOUSE_RE = re.compile(
        r"onMouse(?P<state>Pressed|Released)\s+(?P<button>[LR]):\s*(?P<details>.+)",
        re.IGNORECASE,
    )
    KEY_RE = re.compile(
        r"onKey(?P<state>Pressed|Released)\s+(?P<key>[A-Z0-9]):\s*(?P<details>.+)",
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
        """Parse transcript lines into event objects."""
        events: List[Event] = []
        for idx, raw_line in enumerate(lines, start=1):
            line = raw_line.strip()
            if not line:
                continue
            events.append(self._parse_line(line, len(events)))
        self._assign_deltas(events)
        return events

    def _parse_line(self, line: str, event_index: int) -> Event:
        """Parse a single line into an event object."""
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

        key_match = self.KEY_RE.match(body)
        if key_match:
            state = key_match.group("state").lower()
            key = key_match.group("key")
            action = "key_press" if state == "pressed" else "key_release"
            return Event(
                index=event_index,
                timestamp=timestamp,
                delta=0.0,
                action=action,
                button=key,  # Store key in button field for keyboard events
                window_point=None,
                world_point=None,
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
        """Parse window coordinates from event details."""
        match = self.WINDOW_RE.search(details)
        if not match:
            return None
        x = int(round(float(match.group("x"))))
        y = int(round(float(match.group("y"))))
        return x, y

    def _parse_world(self, details: str) -> Optional[Tuple[float, float]]:
        """Parse world coordinates from event details."""
        match = self.WORLD_RE.search(details)
        if not match:
            return None
        x = float(match.group("x"))
        y = float(match.group("y"))
        return x, y

    def _assign_deltas(self, events: List[Event]) -> None:
        """Assign time deltas between consecutive events."""
        if not events:
            return
        prev_timestamp = 0.0
        for event in events:
            delta = event.timestamp - prev_timestamp
            if delta < 0:
                # Clamp negative deltas to 0
                delta = 0.0
            event.delta = delta
            prev_timestamp = event.timestamp
