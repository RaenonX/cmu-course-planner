"""Shared HTML label/badge helpers used by both the report and suggest renderers."""

import html as html_lib

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


def prereq_info(prerequisites: str) -> str:
    """Collapsible prerequisite popover, or a plain label for None/Unknown."""
    text = prerequisites.strip() if prerequisites else "Unknown"
    if text.lower() == "none":
        return '<span class="no-prereqs">None</span>'
    escaped = html_lib.escape(text)
    return (
        '<details class="prereq-info">'
        '<summary aria-label="Show prerequisites" title="Show prerequisites">i</summary>'
        f'<div class="prereq-popover">{escaped}</div>'
        '</details>'
    )
