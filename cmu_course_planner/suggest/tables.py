from ..common.labels import category_badges, mini_label, prereq_info
from .models import Course
from .render_common import (
    _course_cell, _course_link, _offering_chips, _rating_badge, _time_label,
)
from .time import _selected_meetings

TABLE_HEAD = (
    "<table>\n<thead><tr>"
    '<th>Course</th><th>Title</th><th title="Rating">★</th><th>Category</th>'
    "<th class='units'>Units</th><th>Prereqs</th><th>Time</th><th>Past offerings</th>"
    "</tr></thead>\n<tbody>\n"
)


def _course_row(c: Course, soc: str, prefer: list[str]) -> str:
    offering = c.offering_for(soc)
    minis = offering.minis if offering else []
    selected_minis = [c.selected_mini] if c.selected_mini else minis
    mini_chip = f'<span class="mini-chip">{mini_label(selected_minis)}</span>' if selected_minis else ""
    return (
        f"<tr><td>{_course_link(c, soc)}</td><td>{c.title}{mini_chip}</td>"
        f"<td>{_rating_badge(c, prefer)}</td><td>{category_badges(c.category)}</td>"
        f'<td class="units">{c.units}</td><td>{prereq_info(c.prerequisites)}</td>'
        f'<td class="times">{_time_label(offering, _selected_meetings(c, soc))}</td><td>{_offering_chips(c)}</td></tr>\n'
    )


def _unplaced_row(c: Course, prefer: list[str]) -> str:
    return (
        f"<tr><td>{_course_cell(c, c.last_link())}</td><td>{c.title}</td>"
        f"<td>{_rating_badge(c, prefer)}</td><td>{category_badges(c.category)}</td>"
        f'<td class="units">{c.units}</td><td>{prereq_info(c.prerequisites)}</td>'
        f'<td class="times">{_time_label(c.offered_in[0] if c.offered_in else None)}</td>'
        f"<td>{_offering_chips(c)}</td></tr>\n"
    )


def course_table(sem_courses: list[Course], soc: str, prefer: list[str]) -> str:
    return TABLE_HEAD + "".join(_course_row(c, soc, prefer) for c in sem_courses) + "</tbody></table>\n"


def unplaced_table(unplaced: list[Course], prefer: list[str]) -> str:
    rows = "".join(_unplaced_row(c, prefer) for c in unplaced)
    return '<div class="unplaced">\n<h3>Not placed</h3>\n' + TABLE_HEAD + rows + "</tbody></table>\n</div>\n"
