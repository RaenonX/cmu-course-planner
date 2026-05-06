import re

from .models import Course, Meeting

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

def _add_meeting_intervals(
    intervals_by_day: dict[str, list[tuple[int, int]]],
    meetings: list[Meeting],
) -> None:
    for meeting in meetings:
        begin = _time_minutes(meeting.begin)
        end = _time_minutes(meeting.end)
        if begin is None or end is None or end <= begin:
            continue
        for day in _meeting_days(meeting.days):
            intervals_by_day.setdefault(day, []).append((begin, end))

def _continuity_score(
    courses: list[Course],
    soc_type: str,
    current_time_ranges: list[Meeting],
) -> tuple[int, int]:
    intervals_by_day: dict[str, list[tuple[int, int]]] = {}
    _add_meeting_intervals(intervals_by_day, current_time_ranges)
    for course in courses:
        offering = course.offering_for(soc_type)
        if not offering:
            continue
        _add_meeting_intervals(intervals_by_day, offering.meetings)

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
