import html as html_lib

from ..common.rating import star_rating
from .models import Course, Meeting, Offering

def _category_tag_class(category: str) -> str:
    return "tag-quant" if category == "Quant" else "tag-hft"

def _badges(cats: list[str]) -> str:
    out = []
    for c in cats:
        cls = _category_tag_class(c)
        out.append(f'<span class="tag {cls}">{c}</span>')
    return "".join(out)

def _rating_badge(course: Course, prefer: list[str]) -> str:
    rating = course.effective_rating(prefer)
    return f'<span class="tag tag-rating" title="{rating}/5" aria-label="{rating} out of 5">{star_rating(rating)}</span>'

def _mini_label(minis: list[int]) -> str:
    return "·".join(f"M{n}" for n in minis)

def _meeting_label(meeting: Meeting) -> str:
    return f"{meeting.days} {meeting.begin}-{meeting.end}"

def _format_minutes(minutes: int) -> str:
    hour24 = minutes // 60
    minute = minutes % 60
    meridiem = "AM" if hour24 < 12 else "PM"
    hour12 = hour24 % 12 or 12
    return f"{hour12}:{minute:02d}{meridiem}"

def _time_label(offering: Offering | None) -> str:
    if not offering or not offering.meetings:
        return '<span class="no-prereqs">Unknown</span>'
    labels = ", ".join(_meeting_label(m) for m in offering.meetings)
    return html_lib.escape(labels)

def _offering_chips(course: Course) -> str:
    """Compact chip row for all detected past offerings, oldest → newest."""
    if not course.offered_in:
        return "<em>—</em>"
    parts = ['<div class="chips">']
    for o in reversed(course.offered_in):
        sem_type = o.semester[0]
        mini_html = f'<span class="mini">{_mini_label(o.minis)}</span>' if o.minis else ""
        parts.append(
            f'<a class="chip chip-{sem_type}" href="{o.link}" target="_blank">'
            f'{o.semester}{mini_html}</a>'
        )
    parts.append("</div>")
    return "".join(parts)

def _course_link(c: Course, soc_type: str) -> str:
    href = c.last_link_for(soc_type) or c.last_link()
    if href:
        return f'<a class="course-link" href="{href}" target="_blank">{c.course}</a>'
    return f'<span class="course-plain">{c.course}</span>'

def _prereq_info(prerequisites: str) -> str:
    text = prerequisites.strip() if prerequisites else "Unknown"
    if text.lower() == "none":
        return '<span class="no-prereqs">None</span>'
    escaped = html_lib.escape(text)
    return (
        '<details class="prereq-info">'
        '<summary aria-label="Show prerequisites" title="Show prerequisites">i</summary>'
        f'<div class="prereq-popover">{escaped}</div>'
        '</details>'
    )

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
            mini = f' <span class="mini-chip">{_mini_label(offering.minis)}</span>' if offering.minis else ""
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
