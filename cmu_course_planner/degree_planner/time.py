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
