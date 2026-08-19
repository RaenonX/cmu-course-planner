"""Shared HTML label/badge helpers used by both the report and suggest renderers."""

import html as html_lib

from .prerequisites import PrerequisiteStatus

_CATEGORY_TAG_CLASSES = {"Quant": "tag-quant"}


def category_tag_class(category: str) -> str:
    """CSS class for a category badge."""
    return _CATEGORY_TAG_CLASSES.get(category, "tag-hft")


def category_badges(categories: list[str]) -> str:
    """Inline badge spans for a course's categories."""
    return "".join(
        f'<span class="tag {category_tag_class(c)}">{html_lib.escape(c)}</span>'
        for c in categories
    )


def mini_label(minis: list[int]) -> str:
    """Human-readable mini-slot label, e.g. 'M1·M2' or 'M3'."""
    return "·".join(f"M{n}" for n in minis)


def prereq_info(
    prerequisites: str,
    status: PrerequisiteStatus | None = None,
) -> str:
    """Prerequisite status plus collapsible source text."""
    text = prerequisites.strip() if prerequisites else "Unknown"
    if text.lower() == "none":
        return '<span class="no-prereqs">None</span>'
    if text.lower() == "unknown":
        return '<span class="status-badge status-unknown">Unknown</span>'
    if status == "satisfied":
        label = "Satisfied"
        status_class = "status-success"
        title = "Completed courses satisfy this prerequisite expression"
    elif status == "unknown":
        label = "Unknown"
        status_class = "status-unknown"
        title = "This prerequisite expression could not be evaluated"
    else:
        label = "Unsatisfied"
        status_class = "status-warning"
        title = "Configured completed courses do not satisfy this prerequisite expression"
    escaped = html_lib.escape(text)
    return (
        '<details class="prereq-info">'
        f'<summary aria-label="Show {label.lower()} prerequisites" title="{title}">'
        f'<span class="status-badge {status_class}">{label}</span></summary>'
        f'<div class="prereq-popover">{escaped}</div>'
        '</details>'
    )


def unresolved_time_badge() -> str:
    return (
        '<span class="status-badge status-warning" '
        'title="One or more section meeting times are TBA">TBA / incomplete</span>'
    )
