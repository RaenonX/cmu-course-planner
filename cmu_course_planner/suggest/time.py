import re

from .models import Course, Meeting

SOC_MINIS = {"F": [1, 2], "S": [3, 4], "M": [5, 6]}

_TIME_RE = re.compile(r'(\d{1,2})(?::(\d{2}))?\s*([AP])\.?M\.?', re.IGNORECASE)
_DAY_TOKEN_RE = re.compile(r'Th|Thu|Tu|Tue|Su|Sun|[MTWRFSU]', re.IGNORECASE)
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

def _selected_meetings(course: Course, soc_type: str) -> list[Meeting]:
    offering = course.offering_for(soc_type)
    if not offering:
        return []
    if course.selected_mini is None:
        return offering.meetings
    selected = [m for m in offering.meetings if m.mini is None or m.mini == course.selected_mini]
    return selected or offering.meetings

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
