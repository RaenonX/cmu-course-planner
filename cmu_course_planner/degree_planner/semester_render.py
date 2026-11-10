from ..common.config import SEM_LABEL, USER_TO_SOC
from .models import Course
from .render_common import _semester_available_courses_info


def _semester_heading(
    idx: int,
    sem: str,
    total: int,
    unit_cap: int,
    courses: list[Course],
) -> str:
    soc = USER_TO_SOC[sem]
    underfilled = total != unit_cap
    heading_cls = " semester-heading-underfilled" if underfilled else ""
    unit_cls = " semester-unit-warning" if underfilled else ""
    semester_label = SEM_LABEL[sem]
    return (
        f'<h3 class="semester-heading{heading_cls}">'
        f"Semester {idx + 1} - {semester_label}"
        f' <span class="semester-units{unit_cls}">({total}/{unit_cap} units)</span>'
        f'{_semester_available_courses_info(courses, soc, semester_label)}'
        "</h3>\n"
    )
