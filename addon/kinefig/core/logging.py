"""Structured, bounded in-memory logger for KineFig operations.

Collects recent events for diagnostic bug reporting without persisting
arbitrary scene geometry or exposing sensitive local paths.
"""

from collections import deque
from datetime import datetime, timezone
import traceback
from typing import Optional, Any, Dict, List

# Bounded buffer to prevent unbounded memory growth in long Blender sessions
MAX_LOG_ENTRIES = 100
_LOG_BUFFER: deque = deque(maxlen=MAX_LOG_ENTRIES)
_LAST_ERROR: Optional[Dict[str, Any]] = None


def _format_timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


def _record(level: str, message: str, context: Optional[Dict[str, Any]] = None):
    entry = {
        "timestamp": _format_timestamp(),
        "level": level,
        "message": str(message),
        "context": context or {},
    }
    _LOG_BUFFER.append(entry)


def log_debug(message: str, **context: Any):
    """Log a debug-level event."""
    _record("DEBUG", message, context)


def log_info(message: str, **context: Any):
    """Log an informational operational event (operator start, object created)."""
    _record("INFO", message, context)


def log_warning(message: str, **context: Any):
    """Log an operational warning."""
    _record("WARNING", message, context)


def log_error(message: str, exc: Optional[BaseException] = None, **context: Any):
    """Log an operational error with optional exception traceback."""
    global _LAST_ERROR
    tb_str = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__)) if exc else ""
    ctx = dict(context)
    if tb_str:
        ctx["traceback"] = tb_str

    _record("ERROR", message, ctx)
    _LAST_ERROR = {
        "timestamp": _format_timestamp(),
        "message": str(message),
        "traceback": tb_str,
    }


def get_last_error() -> Optional[Dict[str, Any]]:
    """Return the most recent captured error dict, if any."""
    return _LAST_ERROR


def get_recent_logs() -> List[str]:
    """Return recent log lines formatted as readable strings."""
    lines = []
    for entry in _LOG_BUFFER:
        ts = entry["timestamp"]
        lvl = entry["level"]
        msg = entry["message"]
        ctx = entry["context"]
        ctx_str = f" | {ctx}" if ctx else ""
        lines.append(f"[{ts}] [{lvl}] {msg}{ctx_str}")
    return lines


def get_recent_log_records() -> List[Dict[str, Any]]:
    """Return a copy of recent raw log record dicts."""
    return list(_LOG_BUFFER)


def clear_logs():
    """Reset the log buffer and last error (useful for testing)."""
    global _LAST_ERROR
    _LOG_BUFFER.clear()
    _LAST_ERROR = None
