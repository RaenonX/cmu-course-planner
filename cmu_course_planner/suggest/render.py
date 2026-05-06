import html as html_lib

from ..common.paths import SUGGEST_TEMPLATE_DIR
from .models import Course, Meeting
from .render_panel import _build_schedule_panel


def _suggest_style() -> str:
    return "\n".join(
        (SUGGEST_TEMPLATE_DIR / name).read_text(encoding="utf-8")
        for name in ("suggest_1.css", "suggest_2.css", "suggest_3.css")
    )


def _suggest_head() -> str:
    head = (SUGGEST_TEMPLATE_DIR / "suggest_head.html").read_text(encoding="utf-8")
    return head.replace("{{STYLE}}", _suggest_style())

def build_html(
    semesters: list[str],
    results: list[tuple[str, str, list[tuple[list[list[Course]], list[Course]]]]],
    units_max: int,
    prefer: list[str],
    teaching_location: str,
    snapshot_date: str,
    courses: list[Course],
    current_time_ranges: list[Meeting],
) -> str:
    """
    results: list of (variant_name, variant_desc, routes)
    """
    parts = [_suggest_head()]

    prefer_str = ", ".join(prefer) if prefer else "none"
    parts.append(
        f'<p class="meta">Snapshot: {snapshot_date} &nbsp;·&nbsp; '
        f'Teaching location: {html_lib.escape(teaching_location)} &nbsp;·&nbsp; '
        f'{units_max} units/semester &nbsp;·&nbsp; Category preference: {prefer_str} '
        f'&nbsp;·&nbsp; Scale: ★-★★★★★</p>\n'
    )

    # Tab bar
    parts.append('<div class="tab-bar">\n')
    for i, (name, _, _) in enumerate(results):
        active = " active" if i == 0 else ""
        parts.append(
            f'  <button class="tab-btn{active}" data-tab="{i}">{name}</button>\n'
        )
    parts.append("</div>\n")

    # Tab panels
    for i, (name, desc, routes) in enumerate(results):
        parts.append(
            _build_schedule_panel(
                i,
                name,
                desc,
                semesters,
                routes,
                units_max,
                courses,
                current_time_ranges,
                prefer,
            )
        )

    parts.append((SUGGEST_TEMPLATE_DIR / "suggest_tabs.js").read_text(encoding="utf-8"))
    parts.append((SUGGEST_TEMPLATE_DIR / "suggest_tail.html").read_text(encoding="utf-8"))
    return "".join(parts)
