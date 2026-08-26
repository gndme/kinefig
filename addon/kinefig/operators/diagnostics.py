"""Diagnostic and bug reporting operators for 3D UAT testers."""

import os
import json
import zipfile
import webbrowser
from datetime import datetime, timezone
from pathlib import Path
import bpy

from ..core.diagnostics import (
    format_clipboard_debug_info,
    collect_diagnostic_report,
    generate_github_issue_url,
    get_environment_info,
)
from ..core.logging import get_recent_logs, log_info, log_error


class KINEFIG_OT_copy_debug_info(bpy.types.Operator):
    """Copy safe structured environment & diagnostic info to system clipboard"""

    bl_idname = "kinefig.copy_debug_info"
    bl_label = "Copy Debug Info"
    bl_description = "Copy safe non-sensitive diagnostic info to clipboard for bug reports"

    def execute(self, context):
        try:
            info_text = format_clipboard_debug_info(context)
            context.window_manager.clipboard = info_text
            self.report({"INFO"}, "KineFig debug info copied to clipboard")
            log_info("Diagnostic debug info copied to clipboard")
            return {"FINISHED"}
        except Exception as exc:
            self.report({"ERROR"}, f"Failed to copy debug info: {exc}")
            log_error("Failed to copy debug info", exc=exc)
            return {"CANCELLED"}


class KINEFIG_OT_export_diagnostic_report(bpy.types.Operator):
    """Export a safe diagnostic zip report containing report.json, kinefig.log, and system.txt"""

    bl_idname = "kinefig.export_diagnostic_report"
    bl_label = "Export Diagnostic Report"
    bl_description = "Export non-sensitive diagnostic logs and environment data as a zip archive"

    filepath: bpy.props.StringProperty(
        name="File Path",
        description="Path to export the diagnostic report zip",
        subtype="FILE_PATH",
    ) # type: ignore

    def invoke(self, context, event):
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        self.filepath = f"kinefig-report-{timestamp}.zip"
        context.window_manager.fileselect_add(self)
        return {"RUNNING_MODAL"}

    def execute(self, context):
        try:
            out_path = Path(bpy.path.abspath(self.filepath))
            out_path.parent.mkdir(parents=True, exist_ok=True)

            report_data = collect_diagnostic_report(context)
            recent_logs = get_recent_logs()
            env_info = get_environment_info(context)

            with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED) as zf:
                # 1. report.json
                zf.writestr("report.json", json.dumps(report_data, indent=2))
                # 2. kinefig.log
                zf.writestr("kinefig.log", "\n".join(recent_logs))
                # 3. system.txt
                system_lines = [f"{k}: {v}" for k, v in env_info.items()]
                zf.writestr("system.txt", "\n".join(system_lines))

            self.report({"INFO"}, f"Exported diagnostic report: {out_path.name}")
            log_info(f"Exported diagnostic report to {out_path.name}")
            return {"FINISHED"}
        except Exception as exc:
            self.report({"ERROR"}, f"Failed to export report: {exc}")
            log_error("Failed to export diagnostic report", exc=exc)
            return {"CANCELLED"}


class KINEFIG_OT_report_bug(bpy.types.Operator):
    """Open GitHub Issue Form in default browser with prefilled diagnostic information"""

    bl_idname = "kinefig.report_bug"
    bl_label = "Report Bug on GitHub"
    bl_description = "Open your web browser with a prefilled GitHub issue report"

    issue_title: bpy.props.StringProperty(
        name="Title",
        description="Brief summary of the issue",
        default="",
    ) # type: ignore

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width=400)

    def draw(self, context):
        layout = self.layout
        layout.label(text="Enter a brief summary (or edit on GitHub):")
        layout.prop(self, "issue_title", text="Summary")
        layout.label(text="Safe environment diagnostics will be attached automatically.", icon="INFO")

    def execute(self, context):
        try:
            url = generate_github_issue_url(
                title=self.issue_title,
                context=context,
            )
            webbrowser.open(url)
            self.report({"INFO"}, "Opened GitHub Issue Form in browser")
            log_info("Opened GitHub Issue Form", title=self.issue_title)
            return {"FINISHED"}
        except Exception as exc:
            self.report({"ERROR"}, f"Failed to open browser: {exc}")
            log_error("Failed to open bug report URL", exc=exc)
            return {"CANCELLED"}
