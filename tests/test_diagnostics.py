"""Unit tests for core/diagnostics.py."""

import re
import urllib.parse
from pathlib import Path
from addon.kinefig.core.diagnostics import (
    get_environment_info,
    collect_diagnostic_report,
    format_clipboard_debug_info,
    generate_github_issue_url,
    map_os_for_issue_form,
    map_severity_for_issue_form,
    map_feature_for_issue_form,
    BugReportSenderInterface,
)
from addon.kinefig.core.logging import log_info, log_error, clear_logs

ROOT = Path(__file__).resolve().parents[1]
ISSUE_TEMPLATE_PATH = ROOT / ".github" / "ISSUE_TEMPLATE" / "uat_bug.yml"


def load_yaml_dropdown_options(path: Path) -> dict:
    """Parse dropdown options using pure standard library regex (no pyyaml dependency required)."""
    content = path.read_text(encoding="utf-8")
    dropdowns = {}
    current_id = None
    in_options = False

    for line in content.splitlines():
        id_match = re.match(r"\s*id:\s*([a-zA-Z0-9_]+)", line)
        if id_match:
            current_id = id_match.group(1)
            in_options = False
            continue
        if re.match(r"\s*options:\s*", line):
            in_options = True
            if current_id:
                dropdowns[current_id] = []
            continue
        if in_options:
            opt_match = re.match(r'\s*-\s*["\'](.*?)["\']\s*$', line)
            if opt_match and current_id:
                dropdowns[current_id].append(opt_match.group(1))
            elif not line.strip().startswith("-"):
                in_options = False

    return dropdowns


def test_issue_form_dropdown_options_parity():
    """Verify that diagnostics mapping matches exact options in uat_bug.yml."""
    yaml_dropdowns = load_yaml_dropdown_options(ISSUE_TEMPLATE_PATH)

    # 1. Test OS mapping matches YAML
    mapped_os = map_os_for_issue_form()
    assert mapped_os in yaml_dropdowns["os"], f"Mapped OS '{mapped_os}' not in YAML options: {yaml_dropdowns['os']}"

    # 2. Test Severity mappings match YAML
    for sample in ["blocker", "high", "medium", "low", "nit"]:
        mapped_sev = map_severity_for_issue_form(sample)
        assert mapped_sev in yaml_dropdowns["severity"], f"Mapped severity '{mapped_sev}' not in YAML options"

    # 3. Test Feature mappings match YAML
    for sample in ["smoke", "ball", "double ball", "peg", "hinge", "split", "diagnostics"]:
        mapped_feat = map_feature_for_issue_form(sample)
        assert mapped_feat in yaml_dropdowns["feature"], f"Mapped feature '{mapped_feat}' not in YAML options"


def test_map_feature_semantic_precedence():
    """Verify exact semantic precedence: 'double ball' does not get shadowed by 'ball'."""
    assert map_feature_for_issue_form("ball") == "Ball Joint"
    assert map_feature_for_issue_form("double ball") == "Double Ball / Dumbbell"
    assert map_feature_for_issue_form("Double Ball Joint") == "Double Ball / Dumbbell"
    assert map_feature_for_issue_form("dumbbell") == "Double Ball / Dumbbell"



def test_generate_github_issue_url_privacy():
    """Verify URL does NOT contain local paths or raw tracebacks in query parameters."""
    clear_logs()
    try:
        raise ValueError(r"Local secret path C:\Users\TesterName\test.blend")
    except ValueError as e:
        log_error("Simulated crash", exc=e)

    url = generate_github_issue_url(
        title="Testing bug",
        feature="Foundation / Smoke Test",
        severity="High",
    )

    # Verify query string contains no local user paths
    assert "TesterName" not in url
    assert "C%3A%5CUsers" not in url
    assert "C:\\Users" not in url
    # Verify raw traceback is NOT leaked in URL
    assert "Traceback" not in url


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
        "issue_form_os",
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


def test_bug_report_sender_interface():
    """Verify abstract interface raises NotImplementedError if invoked directly."""
    sender = BugReportSenderInterface()
    try:
        sender.submit_report({})
        assert False, "Should raise NotImplementedError"
    except NotImplementedError:
        pass
