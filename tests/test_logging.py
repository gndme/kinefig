"""Unit tests for core/logging.py."""

import pytest
from addon.kinefig.core.logging import (
    log_debug,
    log_info,
    log_warning,
    log_error,
    get_recent_logs,
    get_recent_log_records,
    get_last_error,
    clear_logs,
    MAX_LOG_ENTRIES,
)


@pytest.fixture(autouse=True)
def clean_log_state():
    """Ensure clean log state before and after each test."""
    clear_logs()
    yield
    clear_logs()


def test_logging_basic_levels():
    """Verify log_debug, log_info, log_warning, log_error record entries."""
    log_debug("Debug test message", param1=42)
    log_info("Info test message", user_action="click")
    log_warning("Warning test message")

    try:
        raise ValueError("Simulated error")
    except ValueError as e:
        log_error("Caught error message", exc=e)

    records = get_recent_log_records()
    assert len(records) == 4

    levels = [r["level"] for r in records]
    assert levels == ["DEBUG", "INFO", "WARNING", "ERROR"]

    # Verify last error was captured
    last_err = get_last_error()
    assert last_err is not None
    assert "Caught error message" in last_err["message"]
    assert "ValueError: Simulated error" in last_err["traceback"]


def test_logging_bounded_buffer():
    """Verify in-memory buffer does not exceed MAX_LOG_ENTRIES (prevents memory leak)."""
    for i in range(MAX_LOG_ENTRIES + 50):
        log_info(f"Message {i}")

    records = get_recent_log_records()
    assert len(records) == MAX_LOG_ENTRIES
    # Should keep the most recent messages
    assert records[-1]["message"] == f"Message {MAX_LOG_ENTRIES + 49}"


def test_get_recent_logs_string_formatting():
    """Verify get_recent_logs returns human-readable formatted strings."""
    log_info("Operator started", op="create_smoke_object")
    lines = get_recent_logs()
    assert len(lines) == 1
    assert "[INFO] Operator started" in lines[0]
    assert "op" in lines[0]
