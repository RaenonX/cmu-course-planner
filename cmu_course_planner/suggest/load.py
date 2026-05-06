import json
from pathlib import Path

import yaml

from ..common.config import SUPPORTED_TEACHING_LOCATION, USER_TO_SOC
from ..common.paths import SNAPSHOT
from ..common.rating import parse_rating
from .models import Course, Meeting, Offering

def load_config(path: Path) -> dict:
    with open(path, encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    for s in cfg.get("semesters", []):
        if s not in USER_TO_SOC:
            raise ValueError(f"Unknown semester '{s}' in config. Use F, S, or Su.")
    if cfg.get("teaching_location") != SUPPORTED_TEACHING_LOCATION:
        raise ValueError(
            f"Unsupported teaching_location {cfg.get('teaching_location')!r}. "
            f"Only {SUPPORTED_TEACHING_LOCATION!r} is supported for now."
        )
    return cfg

def load_current_time_ranges(cfg: dict) -> list[Meeting]:
    meetings = []
    for idx, entry in enumerate(cfg.get("current_time_ranges") or [], start=1):
        try:
            days = entry["days"]
            begin = entry["begin"]
            end = entry["end"]
        except KeyError as exc:
            raise ValueError(f"current_time_ranges item {idx} is missing {exc.args[0]!r}.") from exc
        meetings.append(Meeting(days=str(days), begin=str(begin), end=str(end)))
    return meetings

def load_snapshot(
    config_courses: list[dict],
    prefer: list[str],
    require: bool,
    teaching_location: str,
) -> tuple[list[Course], str]:
    with open(SNAPSHOT, encoding="utf-8") as f:
        data = json.load(f)
    snapshot_date = data.get("generated", "?")
    snapshot_location = data.get("teaching_location")
    if snapshot_location != teaching_location:
        raise ValueError(
            f"Snapshot teaching_location is {snapshot_location!r}, "
            f"but config requires {teaching_location!r}. Run export_report.py first."
        )
    snapshot_courses = {entry["course"]: entry for entry in data["courses"]}
    config_by_course = {entry["course"]: entry for entry in config_courses}
    config_course_ids = list(config_by_course)
    missing_course_ids = [cid for cid in config_course_ids if cid not in snapshot_courses]
    if missing_course_ids:
        missing = ", ".join(missing_course_ids)
        raise ValueError(
            f"Configured course(s) missing from {SNAPSHOT}: {missing}. "
            "Run export_report.py to refresh the course snapshot."
        )

    courses = []
    for cid in config_course_ids:
        entry = snapshot_courses[cid]
        config_entry = config_by_course[cid]
        cats = config_entry.get("category") or []
        rating, rating_by_category = parse_rating(config_entry.get("rating"), cid)
        if require and prefer and not any(c in cats for c in prefer):
            continue
        offerings = [
            Offering(
                semester=o["semester"],
                minis=o.get("minis") or [],
                meetings=[
                    Meeting(
                        days=m.get("days") or "",
                        begin=m.get("begin") or "",
                        end=m.get("end") or "",
                    )
                    for m in (o.get("meetings") or [])
                ],
                link=o["link"],
            )
            for o in (entry.get("offered_in") or [])
        ]
        courses.append(Course(
            course=entry["course"],
            title=entry["title"],
            units=entry["units"],
            prerequisites=entry.get("prerequisites") or "Unknown",
            category=cats,
            rating=rating,
            rating_by_category=rating_by_category,
            offered_in=offerings,
        ))
    return courses, snapshot_date
