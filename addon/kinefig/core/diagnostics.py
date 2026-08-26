"""Diagnostics collector and bug report builder for KineFig.

Collects only safe, non-sensitive environmental and operational data:
- Version and Git commit SHA
- Blender version and OS platform
- Scene unit scale and active mode
- Recent in-memory structured logs (sanitized for export)

Never includes mesh geometry, texture data, .blend files, or local user paths.
GitHub Issue URL only contains high-level environment metadata to prevent
any local path leakage in browser requests.
"""

import sys
import platform
import urllib.parse
from datetime import datetime, timezone
from typing import Dict, Any, Optional

from .build_info import VERSION, COMMIT_SHA, get_version_string, get_short_sha
from .logging import get_recent_logs, get_last_error, sanitize_privacy_text

GITHUB_REPO = "gndme/kinefig"
GITHUB_NEW_ISSUE_URL = f"https://github.com/{GITHUB_REPO}/issues/new"

# Exact dropdown options matching .github/ISSUE_TEMPLATE/uat_bug.yml
SEVERITY_OPTIONS = {
    "blocker": "Blocker (Crash, data corruption, cannot proceed at all)",
    "high": "High (Major joint flaw, broken geometry, missing feature step)",
    "medium": "Medium (Usability issue, incorrect calculation, minor visual defect)",
    "low": "Low / Nit (Small UI typo, suboptimal label, minor styling)",
    "nit": "Low / Nit (Small UI typo, suboptimal label, minor styling)",
}

FEATURE_OPTIONS = {
    "foundation": "Foundation / Smoke Test",
    "smoke": "Foundation / Smoke Test",
    "ball": "Ball Joint",
    "double ball": "Double Ball / Dumbbell",
    "dumbbell": "Double Ball / Dumbbell",
    "peg": "Peg + Socket",
    "socket": "Peg + Socket",
    "hinge": "Hinge / Double Hinge",
    "split": "Split Limb / Torso",
    "diagnostics": "Diagnostics / Bug Reporting",
    "bug": "Diagnostics / Bug Reporting",
    "other": "Other / Unsure",
}


def map_os_for_issue_form() -> str:
    """Map system platform to exact options in uat_bug.yml."""
    sys_name = platform.system()
    if sys_name == "Windows":
        return "Windows"
    elif sys_name == "Linux":
        return "Linux"
    elif sys_name == "Darwin":
        machine = platform.machine().lower()
        if "arm" in machine or "aarch" in machine:
            return "macOS (Apple Silicon)"
        return "macOS (Intel)"
    return "Linux"


def map_severity_for_issue_form(severity: str = "") -> str:
    """Map severity string to exact dropdown option in uat_bug.yml."""
    key = (severity or "medium").strip().lower()
    for prefix, full in SEVERITY_OPTIONS.items():
        if prefix in key:
            return full
    return SEVERITY_OPTIONS["medium"]


def map_feature_for_issue_form(feature: str = "") -> str:
    """Map feature string to exact dropdown option in uat_bug.yml."""
    key = (feature or "foundation").strip().lower()
    for prefix, full in FEATURE_OPTIONS.items():
        if prefix in key:
            return full
    return "Foundation / Smoke Test"


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
        "issue_form_os": map_os_for_issue_form(),
        "blender_mode": mode,
        "scene_unit_scale": unit_scale,
        "active_object_type": active_obj_type,
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
    }


def collect_diagnostic_report(context: Optional[Any] = None, active_feature: str = "") -> Dict[str, Any]:
    """Generate a complete diagnostic report dictionary for export."""
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
    severity: str = "",
    steps: str = "",
    expected: str = "",
    actual: str = "",
    context: Optional[Any] = None,
) -> str:
    """Generate a prefilled URL targeting the GitHub Issue Form (uat_bug.yml).

    PRIVACY GUARANTEE:
    Does NOT put raw logs or tracebacks into URL parameters to prevent
    any potential local path exposure in browser URLs. Only safe environment
    identifiers and mapped dropdown options are included.
    """
    env = get_environment_info(context)
    form_os = map_os_for_issue_form()
    form_severity = map_severity_for_issue_form(severity)
    form_feature = map_feature_for_issue_form(feature)

    last_err = get_last_error()
    err_summary = last_err["message"] if last_err else "None"

    # Only include non-path environment overview in prefilled diagnostics
    safe_diagnostic_summary = (
        f"KineFig: {env['kinefig_version']} ({env['short_sha']})\n"
        f"Blender: {env['blender_version']}\n"
        f"OS: {env['os_platform']}\n"
        f"Mode: {env['blender_mode']}\n"
        f"Unit Scale: {env['scene_unit_scale']}\n"
        f"Last Error: {err_summary}\n"
        f"Note: Detailed logs can be pasted from 'Copy Debug Info' or exported via 'Export Diagnostic Report'."
    )

    # Pre-fill query parameters matching exact uat_bug.yml IDs
    params = {
        "template": "uat_bug.yml",
        "title": f"[UAT BUG] {title}" if title else "[UAT BUG] ",
        "build": f"v{env['kinefig_version']} (Build {env['short_sha']})",
        "blender_version": env["blender_version"],
        "os": form_os,
        "feature": form_feature,
        "severity": form_severity,
        "steps": steps or "1. \n2. \n3. ",
        "expected": expected or "What should have happened",
        "actual": actual or "What actually happened",
        "diagnostics": safe_diagnostic_summary,
    }

    query_str = urllib.parse.urlencode(params, quote_via=urllib.parse.quote)
    return f"{GITHUB_NEW_ISSUE_URL}?{query_str}"


class BugReportSenderInterface:
    """Abstract interface for future remote bug submission through KineFig backend."""

    def submit_report(self, report_data: Dict[str, Any]) -> bool:
        """Submit diagnostic report to the external issue intake endpoint.

        Must NOT contain embedded GitHub tokens or client credentials.
        """
        raise NotImplementedError("Remote backend reporting is not configured for V1 local foundation.")
