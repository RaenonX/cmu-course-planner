import base64
import gzip

from .models import Course, Meeting
from .semester_render import _semester_section
from .tables import unplaced_table


def route_html(
    tab_idx: int,
    route_idx: int,
    semesters: list[str],
    schedule: list[list[Course]],
    unplaced: list[Course],
    units_max: int,
    courses: list[Course],
    current_time_ranges: list[Meeting],
    prefer: list[str],
) -> str:
    parts = [
        _semester_section(
            idx,
            semester,
            schedule[idx],
            units_max,
            courses,
            current_time_ranges,
            prefer,
        )
        for idx, semester in enumerate(semesters)
    ]
    if unplaced:
        parts.append(unplaced_table(
            unplaced,
            prefer,
            f"what-if-{tab_idx}-{route_idx}",
            semesters,
            schedule,
            units_max,
            current_time_ranges,
        ))
    return "".join(parts)


def compressed_route_html(value: str) -> str:
    compressed = gzip.compress(value.encode("utf-8"), compresslevel=9, mtime=0)
    return base64.b64encode(compressed).decode("ascii")
