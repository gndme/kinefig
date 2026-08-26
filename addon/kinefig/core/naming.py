"""Object and data naming helpers for KineFig.

Follows the naming specification defined in AGENTS.md:
- Generated objects: KF_<Category>_<Detail>_<Index> or KF_FigurePart_<Side>_<Part>
- Temporary/scratch objects: _KF_TMP_<Detail>_<Index>
- Deterministic sequential allocation without relying on Blender's fallback .001 suffixes.
"""

import re
from typing import Optional, Iterable

PREFIX_KINEFIG = "KF_"
PREFIX_TEMP = "_KF_TMP_"


def format_object_name(
    category: str,
    detail: str = "",
    side: str = "",
    index: Optional[int] = None,
) -> str:
    """Generate a standardized KineFig object name.

    Examples:
        format_object_name("Joint", "Ball", index=1) -> "KF_Joint_Ball_001"
        format_object_name("FigurePart", "UpperArm", side="L") -> "KF_FigurePart_L_UpperArm"
        format_object_name("Socket", index=1) -> "KF_Socket_001"
    """
    parts = [PREFIX_KINEFIG.rstrip("_"), category]
    if side:
        parts.append(side.upper())
    if detail:
        parts.append(detail)
    if index is not None:
        parts.append(f"{index:03d}")
    return "_".join(parts)


def format_temp_name(descriptor: str, index: Optional[int] = None) -> str:
    """Generate a temporary/helper object name that can be identified and cleaned deterministically."""
    if index is not None:
        return f"{PREFIX_TEMP}{descriptor}_{index:03d}"
    return f"{PREFIX_TEMP}{descriptor}"


def get_next_object_name(
    category: str,
    detail: str = "",
    side: str = "",
    existing_names: Iterable[str] = (),
) -> str:
    """Deterministically allocate the next sequential object name.

    Avoids Blender's fallback `.001` auto-naming.
    If 'KF_Smoke_Ball_001' exists, returns 'KF_Smoke_Ball_002'.
    """
    prefix_without_idx = format_object_name(category=category, detail=detail, side=side)
    pattern = re.compile(rf"^{re.escape(prefix_without_idx)}_(\d+)$")

    used_indices = set()
    for name in existing_names:
        match = pattern.match(name)
        if match:
            used_indices.add(int(match.group(1)))

    next_index = 1
    while next_index in used_indices:
        next_index += 1

    return f"{prefix_without_idx}_{next_index:03d}"


def get_next_temp_name(
    descriptor: str,
    existing_names: Iterable[str] = (),
) -> str:
    """Deterministically allocate the next sequential temporary object name."""
    base_prefix = f"{PREFIX_TEMP}{descriptor}"
    pattern = re.compile(rf"^{re.escape(base_prefix)}_(\d+)$")

    used_indices = set()
    for name in existing_names:
        match = pattern.match(name)
        if match:
            used_indices.add(int(match.group(1)))

    next_index = 1
    while next_index in used_indices:
        next_index += 1

    return f"{base_prefix}_{next_index:03d}"


def is_kinefig_object(name: str) -> bool:
    """Return True if the object name starts with the KineFig prefix or temp prefix."""
    return name.startswith(PREFIX_KINEFIG) or name.startswith(PREFIX_TEMP)


def is_temp_object(name: str) -> bool:
    """Return True if the object is a temporary/scratch KineFig object."""
    return name.startswith(PREFIX_TEMP)


def sanitize_filename(name: str) -> str:
    """Sanitize name for cross-platform file and export systems (e.g. STL export)."""
    # Replace characters forbidden in Windows / POSIX filenames
    cleaned = re.sub(r'[\\/*?:"<>| ]', "_", name)
    # Collapse consecutive underscores
    return re.sub(r"_+", "_", cleaned).strip("_")
