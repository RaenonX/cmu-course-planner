import re

from .models import Course, Meeting

SOC_MINIS = {"F": [1, 2], "S": [3, 4], "M": [5, 6]}

def _time_minutes(value: str) -> int | None:
    m = re.search(r'(\d{1,2})(?::(\d{2}))?\s*([AP])\.?M\.?', value, re.IGNORECASE)
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
    normalized = value.strip()
    if not normalized:
        return []

    if " " in normalized:
        source = re.findall(r'Th|Thu|Tu|Tue|Su|Sun|[MTWRFSU]', normalized, re.IGNORECASE)
    else:
        source = re.findall(r'Th|Thu|Tu|Tue|Su|Sun|[MTWRFSU]', normalized, re.IGNORECASE)

    days = []
    for token in source:
        token_upper = token.upper()
        if token_upper in {"TH", "THU", "R"}:
            day = "R"
        elif token_upper in {"TU", "TUE", "T"}:
            day = "T"
        elif token_upper in {"SU", "SUN", "U"}:
            day = "U"
        else:
            day = token_upper[0]
        if day not in days:
            days.append(day)
    return days

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
        begin = _time_minutes(meeting.begin)
        end = _time_minutes(meeting.end)
        if begin is None or end is None or end <= begin:
            continue
        for day in _meeting_days(meeting.days):
            for bucket in _meeting_buckets(meeting, soc_type):
                intervals_by_day.setdefault((day, bucket), []).append((begin, end))

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
