from dataclasses import dataclass
import re

from ..common.config import normalize_course_id


@dataclass(frozen=True)
class SemesterSchedulerConfig:
    semester: str
    core_courses: tuple[str, ...]
    elective_courses: tuple[str, ...]
    max_elective_units: int
    current_sections: tuple[tuple[str, tuple[str, ...]], ...]


def _course_list(section: dict, name: str) -> tuple[str, ...]:
    values = section.get(name)
    if not isinstance(values, list) or not values or not all(isinstance(value, str) for value in values):
        raise ValueError(f"semester_scheduler.{name} must be a non-empty list of course codes.")
    normalized = tuple(normalize_course_id(value) for value in values)
    if len(set(normalized)) != len(normalized):
        raise ValueError(f"semester_scheduler.{name} contains a duplicate course code.")
    return normalized


_CURRENT_SECTION_RE = re.compile(
    r"^(?P<course>\d{2}-?\d{3})\b.*\((?P<kind>Lecture|Section)\s+(?P<section>[^)]+)\)\s*$"
)


def _current_sections(cfg: dict, core: tuple[str, ...]) -> tuple[tuple[str, tuple[str, ...]], ...]:
    components: dict[str, list[str]] = {course: [] for course in core}
    for entry in cfg.get("current_time_ranges") or []:
        if not isinstance(entry, dict) or not isinstance(entry.get("label"), str):
            continue
        match = _CURRENT_SECTION_RE.fullmatch(entry["label"])
        if not match:
            continue
        course = normalize_course_id(match.group("course"))
        if course not in components:
            continue
        section = match.group("section").strip()
        component = f"Lec {section}" if match.group("kind") == "Lecture" else section
        if component not in components[course]:
            components[course].append(component)
    return tuple((course, tuple(components[course])) for course in core if components[course])


def parse_semester_scheduler_config(cfg: dict) -> SemesterSchedulerConfig:
    section = cfg.get("semester_scheduler")
    if not isinstance(section, dict):
        raise ValueError("Missing semester_scheduler configuration.")
    semester = section.get("semester")
    if not isinstance(semester, str) or not re.fullmatch(r"[FSM]\d{2}", semester):
        raise ValueError("semester_scheduler.semester must be an exact SOC term such as F26.")
    core = _course_list(section, "core_courses")
    electives = _course_list(section, "elective_courses")
    overlap = set(core).intersection(electives)
    if overlap:
        raise ValueError(f"Core and elective courses overlap: {', '.join(sorted(overlap))}.")
    units = section.get("max_elective_units")
    if not isinstance(units, int) or units < 0:
        raise ValueError("semester_scheduler.max_elective_units must be a non-negative integer.")
    return SemesterSchedulerConfig(semester, core, electives, units, _current_sections(cfg, core))
