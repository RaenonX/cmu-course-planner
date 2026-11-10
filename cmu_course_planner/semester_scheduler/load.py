import json
from pathlib import Path

from ..common.paths import SNAPSHOT
from ..common.prerequisites import prerequisite_status
from ..degree_planner.models import Course, Meeting, Offering, SectionOption


def _option(raw: dict) -> SectionOption:
    return SectionOption(
        label=raw["label"],
        meetings=[Meeting(
            days=meeting.get("days") or "",
            begin=meeting.get("begin") or "",
            end=meeting.get("end") or "",
            mini=meeting.get("mini"),
            section=meeting.get("section"),
        ) for meeting in raw.get("meetings") or []],
        mini=raw.get("mini"),
        has_unresolved_time=bool(raw.get("has_unresolved_time")),
        components=tuple(raw.get("components") or [raw["label"]]),
        modality=raw.get("modality") or "in_person",
    )


def load_exact_courses(
    course_ids: tuple[str, ...],
    semester: str,
    completed_courses: list[str],
    snapshot_path: Path = SNAPSHOT,
) -> tuple[list[Course], str]:
    data = json.loads(snapshot_path.read_text(encoding="utf-8"))
    if data.get("section_policy_version") != 1:
        raise ValueError("Course snapshot predates complete-section policies; run export_report.py.")
    if semester not in (data.get("semesters_checked") or []):
        raise ValueError(f"Course snapshot does not include {semester}; run export_report.py.")
    entries = {entry["course"]: entry for entry in data.get("courses") or []}
    courses = []
    for course_id in course_ids:
        entry = entries.get(course_id)
        if entry is None:
            raise ValueError(f"Invalid course code: {course_id} could not be resolved in the CMU SOC.")
        raw_offering = next((item for item in entry.get("offered_in") or [] if item["semester"] == semester), None)
        if raw_offering is None:
            raise ValueError(f"Course {course_id} — {entry['title']} is not offered in {semester}.")
        if not raw_offering.get("section_options"):
            raise ValueError(f"Course {course_id} has no selectable section bundle in {semester}.")
        if not isinstance(entry.get("units"), int) or entry["units"] <= 0:
            raise ValueError(f"Course {course_id} does not have a fixed positive unit count.")
        prerequisites = entry.get("prerequisites") or "Unknown"
        courses.append(Course(
            course=course_id,
            title=entry["title"],
            units=entry["units"],
            prerequisites=prerequisites,
            category=[],
            rating=1,
            rating_by_category={},
            offered_in=[Offering(
                semester=semester,
                minis=raw_offering.get("minis") or [],
                section_options=[_option(option) for option in raw_offering["section_options"]],
                link=raw_offering["link"],
            )],
            prerequisite_status=prerequisite_status(prerequisites, completed_courses),
        ))
    return courses, data.get("generated", "?")
