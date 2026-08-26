"""Unit tests for core/diagnostics.py."""

import urllib.parse
from addon.kinefig.core.diagnostics import (
    get_environment_info,
    collect_diagnostic_report,
    format_clipboard_debug_info,
    generate_github_issue_url,
    BugReportSenderInterface,
)
from addon.kinefig.core.logging import log_info, clear_logs


def test_get_environment_info_safe_fields():
    """Verify environment info collects only safe system fields."""
    env = get_environment_info(context=None)
    required_keys = [
        "kinefig_version",
        "commit_sha",
        "short_sha",
        "blender_version",
        "python_version",
        "os_platform",
        "blender_mode",
        "scene_unit_scale",
        "timestamp",
    ]
    for key in required_keys:
        assert key in env, f"Missing key in environment info: {key}"

    # Verify no private data leaked
    for val in env.values():
        val_str = str(val).lower()
        assert "password" not in val_str
        assert "token" not in val_str
        assert ".blend" not in val_str


def test_collect_diagnostic_report_structure():
    """Verify structured diagnostic report schema."""
    clear_logs()
    log_info("Diagnostic action test", action="test_run")

    report = collect_diagnostic_report(context=None, active_feature="SmokeTest")
    assert report["diagnostic_schema_version"] == "1.0"
    assert report["active_feature"] == "SmokeTest"
    assert "system" in report
    assert len(report["recent_logs"]) >= 1


def test_format_clipboard_debug_info():
    """Verify clipboard format contains essential fields in readable text."""
    text = format_clipboard_debug_info(context=None, active_feature="Smoke")
    assert "KineFig:" in text
    assert "Build:" in text
    assert "OS:" in text
    assert "Active Feature: Smoke" in text


def test_generate_github_issue_url():
    """Verify prefilled GitHub Issue URL points to uat_bug.yml template."""
    url = generate_github_issue_url(
        title="Sphere distortion",
        feature="Smoke",
        severity="High",
        steps="1. Click smoke\n2. See distortion",
        expected="Perfect 10mm sphere",
        actual="Distorted sphere",
        context=None,
    )
    assert url.startswith("https://github.com/gndme/kinefig/issues/new?")

    # Parse query parameters
    parsed = urllib.parse.urlparse(url)
    params = urllib.parse.parse_qs(parsed.query)

    assert params["template"] == ["uat_bug.yml"]
    assert "[UAT BUG] Sphere distortion" in params["title"][0]
    assert params["feature"] == ["Smoke"]
    assert params["severity"] == ["High"]
    assert "diagnostics" in params
    assert "KineFig:" in params["diagnostics"][0]


def test_bug_report_sender_interface():
    """Verify abstract interface raises NotImplementedError if invoked directly."""
    sender = BugReportSenderInterface()
    try:
        sender.submit_report({})
        assert False, "Should raise NotImplementedError"
    except NotImplementedError:
        pass
