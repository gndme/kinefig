"""Diagnostics collector and bug report builder for KineFig.

Collects only safe, non-sensitive environmental and operational data:
- Version and Git commit SHA
- Blender version and OS platform
- Scene unit scale and active mode
- Recent in-memory structured logs
- Last captured error/traceback

Never includes mesh geometry, texture data, .blend files, or unrelated paths.
"""

import sys
import platform
import urllib.parse
from datetime import datetime, timezone
from typing import Dict, Any, Optional

from .build_info import VERSION, COMMIT_SHA, get_version_string, get_short_sha
from .logging import get_recent_logs, get_last_error

GITHUB_REPO = "gndme/kinefig"
GITHUB_NEW_ISSUE_URL = f"https://github.com/{GITHUB_REPO}/issues/new"


def get_environment_info(context: Optional[Any] = None) -> Dict[str, Any]:
    """Collect safe environmental metadata from Blender and the OS."""
    blender_version = "Unknown"
    mode = "Unknown"
    unit_scale = 1.0
    active_obj_type = "None"

    # Safely extract from bpy if running in Blender context
    try:
        import bpy
        blender_version = bpy.app.version_string
        if context is not None:
            if hasattr(context, "mode"):
                mode = context.mode
            if hasattr(context, "scene") and hasattr(context.scene, "unit_settings"):
                unit_scale = getattr(context.scene.unit_settings, "scale_length", 1.0)
            if hasattr(context, "active_object") and context.active_object:
                active_obj_type = getattr(context.active_object, "type", "UNKNOWN")
    except ImportError:
        pass

    return {
        "kinefig_version": VERSION,
        "commit_sha": COMMIT_SHA,
        "short_sha": get_short_sha(),
        "blender_version": blender_version,
        "python_version": platform.python_version(),
        "os_platform": f"{platform.system()} {platform.release()} ({platform.machine()})",
        "blender_mode": mode,
        "scene_unit_scale": unit_scale,
        "active_object_type": active_obj_type,
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
    }


def collect_diagnostic_report(context: Optional[Any] = None, active_feature: str = "") -> Dict[str, Any]:
    """Generate a complete diagnostic report dictionary for export or bug filing."""
    env = get_environment_info(context)
    last_err = get_last_error()
    recent_logs = get_recent_logs()

    return {
        "diagnostic_schema_version": "1.0",
        "system": env,
        "active_feature": active_feature or "None",
        "last_error": last_err or "None",
        "recent_logs": recent_logs,
    }


def format_clipboard_debug_info(context: Optional[Any] = None, active_feature: str = "") -> str:
    """Format safe debug info as human-readable plain text for clipboard copying."""
    env = get_environment_info(context)
    last_err = get_last_error()
    err_summary = last_err["message"] if last_err else "None"

    return (
        f"KineFig: {env['kinefig_version']}\n"
        f"Build: {env['short_sha']}\n"
        f"Blender: {env['blender_version']}\n"
        f"OS: {env['os_platform']}\n"
        f"Mode: {env['blender_mode']}\n"
        f"Unit Scale: {env['scene_unit_scale']}\n"
        f"Active Feature: {active_feature or 'None'}\n"
        f"Last Error: {err_summary}\n"
        f"Timestamp: {env['timestamp']}"
    )


def generate_github_issue_url(
    title: str = "",
    feature: str = "",
    severity: str = "Medium",
    steps: str = "",
    expected: str = "",
    actual: str = "",
    context: Optional[Any] = None,
) -> str:
    """Generate a prefilled URL targeting the GitHub Issue Form (uat_bug.yml)."""
    env = get_environment_info(context)
    debug_text = format_clipboard_debug_info(context, active_feature=feature)
    recent_logs_text = "\n".join(get_recent_logs()[-20:]) if get_recent_logs() else "No logs recorded"

    diagnostic_payload = f"```\n{debug_text}\n\nRecent Logs:\n{recent_logs_text}\n```"

    # Pre-fill query parameters for GitHub Issue Form
    params = {
        "template": "uat_bug.yml",
        "title": f"[UAT BUG] {title}" if title else "[UAT BUG] Issue title",
        "build": env["short_sha"],
        "blender_version": env["blender_version"],
        "os": env["os_platform"],
        "feature": feature or "General",
        "severity": severity,
        "steps": steps or "1. \n2. \n3. ",
        "expected": expected or "What should have happened",
        "actual": actual or "What actually happened",
        "diagnostics": diagnostic_payload,
    }

    query_str = urllib.parse.urlencode(params, quote_via=urllib.parse.quote)
    return f"{GITHUB_NEW_ISSUE_URL}?{query_str}"


# Interface for Future One-Click Remote Backend Submission (Part F Mode 2)
class BugReportSenderInterface:
    """Abstract interface for future remote bug submission through KineFig backend."""

    def submit_report(self, report_data: Dict[str, Any]) -> bool:
        """Submit diagnostic report to the external issue intake endpoint.

        Must NOT contain embedded GitHub tokens or client credentials.
        """
        raise NotImplementedError("Remote backend reporting is not configured for V1 local foundation.")
