import html as html_lib
import json

from .models import Course, Meeting
from .route_payload import compressed_route_html, route_html
from .route_tree import route_tree
from .semester_render import _semester_section


def _build_schedule_panel(
    tab_idx: int,
    variant_name: str,
    variant_desc: str,
    semesters: list[str],
    routes: list[tuple[list[list[Course]], list[Course]]],
    unit_caps: list[int],
    courses: list[Course],
    current_time_ranges: list[Meeting],
    prefer: list[str],
) -> str:
    active = " active" if tab_idx == 0 else ""
    parts = [f'<div id="tab-{tab_idx}" class="tab-panel{active}">\n']
    parts.append(f'<p class="variant-desc">{html_lib.escape(variant_desc)}</p>\n')
    parts.append(f'<p class="route-count">{len(routes)} route{"s" if len(routes) != 1 else ""}</p>\n')
    parts.append(
        '<div class="route-layout"><nav class="route-browser" aria-label="Schedule route selection">'
        '<h2>Schedule tree</h2>'
        '<p class="meta">Expand semester course sets, then choose an exact section route.</p>'
        f'{route_tree(routes, prefer)}</nav>'
    )
    payloads = [
        compressed_route_html(route_html(
            tab_idx,
            route_idx,
            semesters,
            schedule,
            unplaced,
            unit_caps,
            courses,
            current_time_ranges,
            prefer,
        ))
        for route_idx, (schedule, unplaced) in enumerate(routes, start=1)
    ]
    parts.append('<section class="route-panel" aria-live="polite"></section></div>\n')
    parts.append(
        '<script type="application/json" class="route-data">'
        f'{json.dumps(payloads, separators=(",", ":"))}</script>\n'
    )
    parts.append("</div>\n")
    return "".join(parts)
