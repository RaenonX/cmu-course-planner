import html as html_lib
from .models import Course, Meeting
from .render_common import _format_minutes
from .time import _meeting_days, _selected_meetings, _time_minutes
def _timeline_entries(
    sem_courses: list[Course],
    soc_type: str,
    current_time_ranges: list[Meeting],
) -> dict[str, list[tuple[int, int, str, str]]]:
    merged: dict[tuple[str, int, int], tuple[list[str], set[str]]] = {}
    def add_entry(day: str, begin: int, end: int, label: str, cls: str) -> None:
        labels, classes = merged.setdefault((day, begin, end), ([], set()))
        if label in labels:
            return
        labels.append(label)
        classes.add(cls)
    for meeting in current_time_ranges:
        begin = _time_minutes(meeting.begin)
        end = _time_minutes(meeting.end)
        if begin is None or end is None or end <= begin:
            continue
        for day in _meeting_days(meeting.days):
            mini = f" M{meeting.mini}" if meeting.mini else ""
            add_entry(day, begin, end, f"Current{mini}", "timeline-current")
    for course in sem_courses:
        offering = course.offering_for(soc_type)
        if not offering:
            continue
        for meeting in _selected_meetings(course, soc_type):
            begin = _time_minutes(meeting.begin)
            end = _time_minutes(meeting.end)
            if begin is None or end is None or end <= begin:
                continue
            mini = f" M{meeting.mini}" if meeting.mini else ""
            label = f"{course.course}{mini} {course.title}"
            for day in _meeting_days(meeting.days):
                add_entry(day, begin, end, label, "timeline-course")
    entries: dict[str, list[tuple[int, int, str, str]]] = {}
    for (day, begin, end), (labels, classes) in merged.items():
        cls = "timeline-overlap" if len(classes) > 1 else next(iter(classes))
        entries.setdefault(day, []).append((begin, end, " / ".join(labels), cls))
    for day_entries in entries.values():
        day_entries.sort(key=lambda entry: (entry[0], entry[1], entry[2]))
    return entries
def _semester_timeline(
    sem_courses: list[Course],
    soc_type: str,
    current_time_ranges: list[Meeting],
) -> str:
    entries = _timeline_entries(sem_courses, soc_type, current_time_ranges)
    if not entries:
        return '<p class="timeline-empty">No meeting times detected.</p>'
    all_ranges = [entry for day_entries in entries.values() for entry in day_entries]
    timeline_begin = min(entry[0] for entry in all_ranges)
    timeline_end = max(entry[1] for entry in all_ranges)
    span = max(timeline_end - timeline_begin, 1)
    day_labels = [("M", "Mon"), ("T", "Tue"), ("W", "Wed"), ("R", "Thu"), ("F", "Fri"), ("U", "Sun")]
    parts = [
        '<div class="timeline">',
        '<div class="timeline-scale">',
        f'<span>{_format_minutes(timeline_begin)}</span>',
        f'<span>{_format_minutes(timeline_end)}</span>',
        '</div>',
    ]
    for day, label in day_labels:
        if day not in entries:
            continue
        lane_ends: list[int] = []
        bars = []
        for begin, end, entry_label, cls in entries[day]:
            lane = next((idx for idx, lane_end in enumerate(lane_ends) if begin >= lane_end), None)
            if lane is None:
                lane = len(lane_ends)
                lane_ends.append(end)
            else:
                lane_ends[lane] = end
            left = ((begin - timeline_begin) / span) * 100
            width = max(((end - begin) / span) * 100, 1.5)
            title = html_lib.escape(
                f"{entry_label}: {_format_minutes(begin)}-{_format_minutes(end)}",
                quote=True,
            )
            bars.append(
                f'<div class="timeline-bar {cls}" title="{title}" '
                f'style="--left:{left:.3f}%;--width:{width:.3f}%;--lane:{lane};">'
                f'<span class="timeline-time">{_format_minutes(begin)}-{_format_minutes(end)}</span>'
                f'<span class="timeline-label">{html_lib.escape(entry_label)}</span>'
                '</div>'
            )
        parts.append(
            f'<div class="timeline-day"><div class="timeline-day-label">{label}</div>'
            f'<div class="timeline-track" style="--lanes:{len(lane_ends)};">'
        )
        parts.extend(bars)
        parts.append('</div></div>')
    parts.append('</div>')
    return "".join(parts)
