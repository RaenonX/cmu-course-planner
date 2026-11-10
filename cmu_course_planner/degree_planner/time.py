import re

from .models import Course, Meeting, SectionOption

SOC_MINIS = {"F": [1, 2], "S": [3, 4], "M": [5, 6]}

_TIME_RE = re.compile(r'(\d{1,2})(?::(\d{2}))?\s*([AP])\.?M\.?', re.IGNORECASE)
_DAY_TOKEN_RE = re.compile(r'Thu|Th|Tue|Tu|Sun|Su|[MTWRFSU]', re.IGNORECASE)
# Day tokens that do not map to their own first letter (e.g. "Th"/"Thu" -> "R").
_DAY_ALIASES = {
    "TH": "R", "THU": "R", "R": "R",
    "TU": "T", "TUE": "T", "T": "T",
    "SU": "U", "SUN": "U", "U": "U",
}

def _time_minutes(value: str) -> int | None:
    m = _TIME_RE.search(value)
    if not m:
        return None
    hour = int(m.group(1))
    minute = int(m.group(2) or 0)
    meridiem = m.group(3).upper()
    if meridiem == "P" and hour != 12:
        hour += 12
    elif meridiem == "A" and hour == 12:
        hour = 0
    return hour * 60 + minute

def _meeting_days(value: str) -> list[str]:
    days: list[str] = []
    for token in _DAY_TOKEN_RE.findall(value):
        day = _DAY_ALIASES.get(token.upper(), token[0].upper())
        if day not in days:
            days.append(day)
    return days

def _meeting_interval(meeting: Meeting) -> tuple[int, int] | None:
    """(begin, end) in minutes, or None when unparseable or non-positive length."""
    begin = _time_minutes(meeting.begin)
    end = _time_minutes(meeting.end)
    if begin is None or end is None or end <= begin:
        return None
    return begin, end

def _meeting_buckets(meeting: Meeting, soc_type: str) -> list[int]:
    if meeting.mini is not None:
        return [meeting.mini]
    return SOC_MINIS.get(soc_type, [0])

def _selected_section_option(course: Course, soc_type: str) -> SectionOption | None:
    offering = course.offering_for(soc_type)
    if not offering:
        return None
    if course.selected_section is not None:
        return next(
            (
                option for option in offering.section_options
                if option.label == course.selected_section
                and (course.selected_mini is None or option.mini == course.selected_mini)
            ),
            None,
        )
    eligible = [
        option for option in offering.section_options
        if course.selected_mini is None or option.mini == course.selected_mini
    ]
    return eligible[0] if len(eligible) == 1 else None


def _selected_meetings(course: Course, soc_type: str) -> list[Meeting]:
    option = _selected_section_option(course, soc_type)
    return option.meetings if option else []

def _add_meeting_intervals_by_bucket(
    intervals_by_day: dict[tuple[str, int], list[tuple[int, int]]],
    meetings: list[Meeting],
    soc_type: str,
) -> None:
    for meeting in meetings:
        interval = _meeting_interval(meeting)
        if interval is None:
            continue
        for day in _meeting_days(meeting.days):
            for bucket in _meeting_buckets(meeting, soc_type):
                intervals_by_day.setdefault((day, bucket), []).append(interval)

def _continuity_score(
    courses: list[Course],
    soc_type: str,
    current_time_ranges: list[Meeting],
) -> tuple[int, int]:
    intervals_by_day: dict[tuple[str, int], list[tuple[int, int]]] = {}
    _add_meeting_intervals_by_bucket(intervals_by_day, current_time_ranges, soc_type)
    for course in courses:
        _add_meeting_intervals_by_bucket(intervals_by_day, _selected_meetings(course, soc_type), soc_type)

    gap = 0
    overlap = 0
    for intervals in intervals_by_day.values():
        intervals.sort()
        previous_end: int | None = None
        for begin, end in intervals:
            if previous_end is not None:
                if begin > previous_end:
                    gap += begin - previous_end
                elif begin < previous_end:
                    overlap += previous_end - begin
            previous_end = max(previous_end or end, end)
    return overlap, gap


def course_time_conflicts(
    course: Course,
    soc_type: str,
    selected_courses: list[Course],
    current_time_ranges: list[Meeting],
) -> list[str]:
    """Describe meetings that overlap the course's selected section."""
    conflicts: list[str] = []
    candidate_meetings = _selected_meetings(course, soc_type)
    existing = [
        (meeting.label or "Current commitment", meeting)
        for meeting in current_time_ranges
    ]
    for selected in selected_courses:
        existing.extend(
            (selected.course, meeting)
            for meeting in _selected_meetings(selected, soc_type)
        )

    for candidate in candidate_meetings:
        candidate_interval = _meeting_interval(candidate)
        if candidate_interval is None:
            continue
        candidate_days = set(_meeting_days(candidate.days))
        candidate_buckets = set(_meeting_buckets(candidate, soc_type))
        for label, meeting in existing:
            interval = _meeting_interval(meeting)
            if interval is None:
                continue
            if not candidate_days.intersection(_meeting_days(meeting.days)):
                continue
            if not candidate_buckets.intersection(_meeting_buckets(meeting, soc_type)):
                continue
            if candidate_interval[0] < interval[1] and interval[0] < candidate_interval[1]:
                conflict = f"{label} ({meeting.days} {meeting.begin}–{meeting.end})"
                if conflict not in conflicts:
                    conflicts.append(conflict)
    return conflicts
