import html as html_lib

from ..common.labels import mini_label, prereq_info
from ..common.rating import star_rating
from .models import Course, Meeting, Offering
from .time import _selected_meetings

def _rating_badge(course: Course, prefer: list[str]) -> str:
    rating = course.effective_rating(prefer)
    return f'<span class="tag tag-rating" title="{rating}/5" aria-label="{rating} out of 5">{star_rating(rating)}</span>'

def _meeting_label(meeting: Meeting) -> str:
    return f"{meeting.days} {meeting.begin}-{meeting.end}"

def _format_minutes(minutes: int) -> str:
    hour24 = minutes // 60
    minute = minutes % 60
    meridiem = "AM" if hour24 < 12 else "PM"
    hour12 = hour24 % 12 or 12
    return f"{hour12}:{minute:02d}{meridiem}"

def _time_label(offering: Offering | None, meetings: list[Meeting] | None = None) -> str:
    selected = meetings if meetings is not None else (offering.meetings if offering else [])
    if not offering or not selected:
        return '<span class="no-prereqs">Unknown</span>'
    labels = ", ".join(_meeting_label(m) for m in selected)
    return html_lib.escape(labels)

def _offering_chips(course: Course) -> str:
    """Compact chip row for all detected past offerings, oldest → newest."""
    if not course.offered_in:
        return "<em>—</em>"
    parts = ['<div class="chips">']
    for o in reversed(course.offered_in):
        sem_type = o.semester[0]
        mini_html = f'<span class="mini">{mini_label(o.minis)}</span>' if o.minis else ""
        parts.append(
            f'<a class="chip chip-{sem_type}" href="{o.link}" target="_blank">'
            f'{o.semester}{mini_html}</a>'
        )
    parts.append("</div>")
    return "".join(parts)

def _course_cell(course: Course, href: str | None) -> str:
    if href:
        return f'<a class="course-link" href="{href}" target="_blank">{course.course}</a>'
    return f'<span class="course-plain">{course.course}</span>'

def _course_link(c: Course, soc_type: str) -> str:
    return _course_cell(c, c.last_link_for(soc_type) or c.last_link())

def _semester_available_courses_info(courses: list[Course], soc_type: str, semester_label: str) -> str:
    available = sorted(
        (course for course in courses if course.offering_for(soc_type)),
        key=lambda course: course.course,
    )
    if not available:
        body = '<p class="empty">No detected offerings.</p>'
    else:
        rows = []
        for course in available:
            offering = course.offering_for(soc_type)
            assert offering is not None
            mini = f' <span class="mini-chip">{mini_label(offering.minis)}</span>' if offering.minis else ""
            rows.append(
                '<li>'
                f'{_course_link(course, soc_type)}'
                f' <span class="available-title">{html_lib.escape(course.title)}</span>'
                f'{mini}'
                f' <span class="available-time">{_time_label(offering, _selected_meetings(course, soc_type))}</span>'
                '</li>'
            )
        body = f'<ul class="available-list">{"".join(rows)}</ul>'
    return (
        '<details class="semester-offerings-info">'
        f'<summary aria-label="Show all {html_lib.escape(semester_label)} offerings" '
        f'title="Show all {html_lib.escape(semester_label)} offerings">◷</summary>'
        f'<div class="semester-offerings-popover"><strong>Available in {html_lib.escape(semester_label)}</strong>{body}</div>'
        '</details>'
    )
