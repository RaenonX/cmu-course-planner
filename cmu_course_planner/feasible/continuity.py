from ..suggest.time import (
    SOC_MINIS,
    _add_meeting_intervals_by_bucket,
)
from .models import FeasibleSchedule


TRANSITION_MINUTES = 10
DAY_ORDER = ("M", "T", "W", "R", "F", "S", "U")


def _range_and_gap(intervals: list[tuple[int, int]]) -> tuple[int, int, int]:
    ordered = sorted(intervals)
    range_begin = ordered[0][0]
    range_end = ordered[0][1]
    gap_minutes = 0
    for begin, end in ordered[1:]:
        if begin > range_end:
            gap_minutes += max(begin - range_end - TRANSITION_MINUTES, 0)
        range_end = max(range_end, end)
    return range_begin, range_end, gap_minutes


def schedule_continuity(schedule: FeasibleSchedule, semester: str) -> dict:
    soc_type = semester[0]
    intervals_by_day: dict[tuple[str, int], list[tuple[int, int]]] = {}
    for choice in schedule.choices:
        _add_meeting_intervals_by_bucket(
            intervals_by_day,
            choice.option.meetings,
            soc_type,
        )

    mini_data = []
    total_gap_minutes = 0
    max_gap_minutes = 0
    for mini in SOC_MINIS[soc_type]:
        grouped: dict[tuple[int, int, int], list[str]] = {}
        for day in DAY_ORDER:
            intervals = intervals_by_day.get((day, mini))
            if not intervals:
                continue
            metrics = _range_and_gap(intervals)
            grouped.setdefault(metrics, []).append(day)
            total_gap_minutes += metrics[2]
            max_gap_minutes = max(max_gap_minutes, metrics[2])
        mini_data.append({
            "mini": mini,
            "groups": [
                {
                    "days": days,
                    "beginMinutes": begin,
                    "endMinutes": end,
                    "gapMinutes": gap,
                }
                for (begin, end, gap), days in grouped.items()
            ],
        })
    return {
        "minis": mini_data,
        "totalGapMinutes": total_gap_minutes,
        "maxGapMinutes": max_gap_minutes,
    }
