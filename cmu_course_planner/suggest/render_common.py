import html as html_lib

from ..common.labels import mini_label, unresolved_time_badge
from ..common.rating import star_rating
from .models import Course, Meeting, Offering, SectionOption

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

def _section_option_label(option: SectionOption) -> str:
    labels = ", ".join(_meeting_label(meeting) for meeting in option.meetings)
    time_html = html_lib.escape(labels) if labels else '<span class="no-prereqs">Unknown</span>'
    if option.has_unresolved_time:
        time_html += f" {unresolved_time_badge()}"
    mini = f"M{option.mini} " if option.mini else ""
    return f'<span class="section-label">{mini}{html_lib.escape(option.label)}</span>: {time_html}'


def _time_label(offering: Offering | None, option: SectionOption | None = None) -> str:
    if not offering:
        return '<span class="no-prereqs">Unknown</span>'
    if option is not None:
        return _section_option_label(option)
    return "<br>".join(_section_option_label(item) for item in offering.section_options)

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
                f' <span class="available-time">{_time_label(offering)}</span>'
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
