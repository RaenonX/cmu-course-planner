from ..common.config import SEM_LABEL, USER_TO_SOC
from .models import Course, Meeting
from .render_common import _semester_available_courses_info
from .tables import course_table
from .timeline import _semester_timeline
from .units import semester_unit_total


def _semester_heading(
    idx: int,
    sem: str,
    total: int,
    units_max: int,
    courses: list[Course],
) -> str:
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


def _semester_section(
    idx: int,
    sem: str,
    sem_courses: list[Course],
    units_max: int,
    courses: list[Course],
    current_time_ranges: list[Meeting],
    prefer: list[str],
) -> str:
    soc = USER_TO_SOC[sem]
    total = semester_unit_total(sem_courses)
    parts = [_semester_heading(idx, sem, total, units_max, courses)]
    if idx == 0:
        parts.append(_semester_timeline(sem_courses, soc, current_time_ranges))
    if sem_courses:
        parts.append(course_table(sem_courses, soc, prefer))
    else:
        parts.append('<p class="empty">No courses assigned.</p>\n')
    return "".join(parts)
