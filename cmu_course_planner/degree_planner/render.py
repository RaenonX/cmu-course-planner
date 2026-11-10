import html
import json

from ..common.paths import DEGREE_PLANNER_TEMPLATE_DIR
from .render_panel import build_schedule_panel
from .route_payload import build_path_data
from .variants import VARIANTS


def _degree_planner_style() -> str:
    return "\n".join((DEGREE_PLANNER_TEMPLATE_DIR / name).read_text(encoding="utf-8")
                     for name in ("degree_planner_1.css", "degree_planner_2.css",
                                  "degree_planner_3.css", "course_roles.css", "course_preferences.css"))


def build_html(courses, semesters, unit_caps, prefer, teaching_location, snapshot_date, current) -> str:
    head = (DEGREE_PLANNER_TEMPLATE_DIR / "degree_planner_head.html").read_text(encoding="utf-8")
    parts = [head.replace("{{STYLE}}", _degree_planner_style())]
    parts.append(
        f'<p class="meta">Snapshot: {html.escape(snapshot_date)} · '
        f'Teaching location: {html.escape(teaching_location)} · '
        f'Unit caps: {" / ".join(map(str, unit_caps))} · '
        f'Category preference: {html.escape(", ".join(prefer) or "none")}</p>'
    )
    parts.append('<div class="tab-bar">')
    for index, (name, _) in enumerate(VARIANTS):
        active = " active" if index == 0 else ""
        parts.append(f'<button class="tab-btn{active}" data-tab="{index}">{name}</button>')
    parts.append('</div>')
    parts.extend(build_schedule_panel(i, name, desc, courses)
                 for i, (name, desc) in enumerate(VARIANTS))
    data = json.dumps(build_path_data(courses, semesters, unit_caps, prefer, current),
                      separators=(",", ":"), ensure_ascii=False).replace("<", "\\u003c")
    parts.append(f'<script type="application/json" id="degree-path-data">{data}</script>')
    worker = "\n".join((DEGREE_PLANNER_TEMPLATE_DIR / name).read_text(encoding="utf-8")
                       for name in ("planner_constraints.js", "planner_search.js",
                                    "planner_what_if.js", "planner_worker.js"))
    parts.append(f'<script type="text/plain" id="degree-worker-source">{worker}</script>')
    for name in ("degree_planner_worker.js", "degree_planner_timeline.js", "degree_planner_tree.js", "degree_planner_filters.js", "degree_planner_tabs.js",
                 "degree_planner_tail.html"):
        parts.append((DEGREE_PLANNER_TEMPLATE_DIR / name).read_text(encoding="utf-8"))
    return "".join(parts)
