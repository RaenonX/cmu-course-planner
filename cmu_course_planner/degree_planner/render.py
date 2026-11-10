import html as html_lib

from ..common.paths import DEGREE_PLANNER_TEMPLATE_DIR
from .models import Course, Meeting
from .render_panel import _build_schedule_panel


def _degree_planner_style() -> str:
    return "\n".join(
        (DEGREE_PLANNER_TEMPLATE_DIR / name).read_text(encoding="utf-8")
        for name in ("degree_planner_1.css", "degree_planner_2.css", "degree_planner_3.css", "course_roles.css", "course_preferences.css")
    )


def _degree_planner_head() -> str:
    head = (DEGREE_PLANNER_TEMPLATE_DIR / "degree_planner_head.html").read_text(encoding="utf-8")
    return head.replace("{{STYLE}}", _degree_planner_style())

def build_html(
    semesters: list[str],
    results: list[tuple[str, str, list[tuple[list[list[Course]], list[Course]]]]],
    unit_caps: list[int],
    prefer: list[str],
    teaching_location: str,
    snapshot_date: str,
    courses: list[Course],
    current_time_ranges: list[Meeting],
) -> str:
    """
    results: list of (variant_name, variant_desc, routes)
    """
    parts = [_degree_planner_head()]

    prefer_str = ", ".join(prefer) if prefer else "none"
    parts.append(
        f'<p class="meta">Snapshot: {snapshot_date} &nbsp;·&nbsp; '
        f'Teaching location: {html_lib.escape(teaching_location)} &nbsp;·&nbsp; '
        f'Unit caps: {" / ".join(str(cap) for cap in unit_caps)} &nbsp;·&nbsp; '
        f'Category preference: {prefer_str} '
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
                unit_caps,
                courses,
                current_time_ranges,
                prefer,
            )
        )

    parts.append((DEGREE_PLANNER_TEMPLATE_DIR / "degree_planner_filters.js").read_text(encoding="utf-8"))
    parts.append((DEGREE_PLANNER_TEMPLATE_DIR / "degree_planner_tabs.js").read_text(encoding="utf-8"))
    parts.append((DEGREE_PLANNER_TEMPLATE_DIR / "degree_planner_tail.html").read_text(encoding="utf-8"))
    return "".join(parts)
