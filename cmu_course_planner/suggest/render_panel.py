import html as html_lib

from ..common.config import SEM_LABEL, USER_TO_SOC
from .models import Course, Meeting
from .render_common import _semester_available_courses_info
from .route_labels import _route_tab_label
from .tables import course_table, unplaced_table
from .timeline import _semester_timeline


def _semester_heading(idx: int, sem: str, total: int, units_max: int, courses: list[Course]) -> str:
    soc = USER_TO_SOC[sem]
    underfilled = total != units_max
    heading_cls = " semester-heading-underfilled" if underfilled else ""
    unit_cls = " semester-unit-warning" if underfilled else ""
    semester_label = SEM_LABEL[sem]
    return (
        f'<h3 class="semester-heading{heading_cls}">'
        f"Semester {idx + 1} - {semester_label}"
        f' <span class="semester-units{unit_cls}">({total}/{units_max} units)</span>'
        f'{_semester_available_courses_info(courses, soc, semester_label)}'
        "</h3>\n"
    )


def _route_tabs(tab_idx: int, routes: list[tuple[list[list[Course]], list[Course]]], prefer: list[str]) -> str:
    parts = ['<div class="route-tab-bar">\n']
    for route_idx, (schedule, _) in enumerate(routes, start=1):
        active_route = " active" if route_idx == 1 else ""
        route_panel_id = f"tab-{tab_idx}-route-{route_idx}"
        parts.append(
            f'<button class="route-tab-btn{active_route}" data-route-panel="{route_panel_id}" '
            f'aria-label="{html_lib.escape(f"Route {route_idx}")}">'
            f'{_route_tab_label(schedule, prefer)}</button>\n'
        )
    parts.append("</div>\n")
    return "".join(parts)


def _semester_section(idx: int, sem: str, sem_courses: list[Course], units_max: int, courses: list[Course], current_time_ranges: list[Meeting], prefer: list[str]) -> str:
    soc = USER_TO_SOC[sem]
    total = sum(c.units for c in sem_courses)
    parts = [_semester_heading(idx, sem, total, units_max, courses)]
    if idx == 0:
        parts.append(_semester_timeline(sem_courses, soc, current_time_ranges))
    if not sem_courses:
        parts.append('<p class="empty">No courses assigned.</p>\n')
    else:
        parts.append(course_table(sem_courses, soc, prefer))
    return "".join(parts)


def _build_schedule_panel(
    tab_idx: int,
    variant_name: str,
    variant_desc: str,
    semesters: list[str],
    routes: list[tuple[list[list[Course]], list[Course]]],
    units_max: int,
    courses: list[Course],
    current_time_ranges: list[Meeting],
    prefer: list[str],
) -> str:
    active = " active" if tab_idx == 0 else ""
    parts = [f'<div id="tab-{tab_idx}" class="tab-panel{active}">\n']
    parts.append(f'<p class="variant-desc">{html_lib.escape(variant_desc)}</p>\n')
    parts.append(f'<p class="route-count">{len(routes)} route{"s" if len(routes) != 1 else ""}</p>\n')
    parts.append(_route_tabs(tab_idx, routes, prefer))
    for route_idx, (schedule, unplaced) in enumerate(routes, start=1):
        active_route = " active" if route_idx == 1 else ""
        parts.append(f'<section id="tab-{tab_idx}-route-{route_idx}" class="route-panel{active_route}">\n')
        for idx, sem in enumerate(semesters):
            parts.append(_semester_section(idx, sem, schedule[idx], units_max, courses, current_time_ranges, prefer))
        if unplaced:
            parts.append(unplaced_table(unplaced, prefer))
        parts.append("</section>\n")
    parts.append("</div>\n")
    return "".join(parts)
