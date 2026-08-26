"""KineFig core module."""

from .units import MM_TO_M, mm_to_blender, blender_to_mm
from .errors import KineFigError, KineFigValidationError
from .validation import (
    require_positive,
    require_non_negative,
    require_in_range,
    validate_ball_joint_parameters,
)

from .naming import (
    PREFIX_KINEFIG,
    PREFIX_TEMP,
    format_object_name,
    format_temp_name,
    get_next_object_name,
    get_next_temp_name,
    is_kinefig_object,
    is_temp_object,
    sanitize_filename,
)
from .build_info import (
    VERSION,
    COMMIT_SHA,
    get_version_string,
    get_short_sha,
)
from .logging import (
    log_debug,
    log_info,
    log_warning,
    log_error,
    get_recent_logs,
    get_recent_log_records,
    get_last_error,
    clear_logs,
)
from .diagnostics import (
    get_environment_info,
    collect_diagnostic_report,
    format_clipboard_debug_info,
    generate_github_issue_url,
    BugReportSenderInterface,
)

__all__ = [
    "MM_TO_M",
    "mm_to_blender",
    "blender_to_mm",
    "KineFigError",
    "KineFigValidationError",
    "require_positive",
    "require_non_negative",
    "require_in_range",
    "validate_ball_joint_parameters",

    "PREFIX_KINEFIG",
    "PREFIX_TEMP",
    "format_object_name",
    "format_temp_name",
    "get_next_object_name",
    "get_next_temp_name",
    "is_kinefig_object",
    "is_temp_object",
    "sanitize_filename",
    "VERSION",
    "COMMIT_SHA",
    "get_version_string",
    "get_short_sha",
    "log_debug",
    "log_info",
    "log_warning",
    "log_error",
    "get_recent_logs",
    "get_recent_log_records",
    "get_last_error",
    "clear_logs",
    "get_environment_info",
    "collect_diagnostic_report",
    "format_clipboard_debug_info",
    "generate_github_issue_url",
    "BugReportSenderInterface",
]
