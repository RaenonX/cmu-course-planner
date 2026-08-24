import html as html_lib
import json
from pathlib import Path

from ..suggest.render import _suggest_style
from ..suggest.time import SOC_MINIS, _meeting_days, _meeting_interval
from .config import FeasibleConfig
from .continuity import schedule_continuity
from .models import CourseChoice, FeasibleSchedule


def _choice_key(choice: CourseChoice) -> tuple:
    return choice.course.course, choice.option.label, choice.is_core


def _choice_data(choice: CourseChoice) -> dict:
    course, option = choice.course, choice.option
    meetings_by_time: dict[tuple, dict] = {}
    for meeting in option.meetings:
        interval = _meeting_interval(meeting)
        days = _meeting_days(meeting.days)
        key = (tuple(days), meeting.begin, meeting.end, meeting.mini)
        section = meeting.section or option.label
        if key in meetings_by_time:
            if section not in meetings_by_time[key]["sections"]:
                meetings_by_time[key]["sections"].append(section)
            continue
        meetings_by_time[key] = {
            "sections": [section],
            "days": _meeting_days(meeting.days),
            "daysLabel": meeting.days,
            "begin": meeting.begin,
            "end": meeting.end,
            "beginMinutes": interval[0] if interval else None,
            "endMinutes": interval[1] if interval else None,
            "mini": meeting.mini,
        }
    meetings = []
    for meeting in meetings_by_time.values():
        sections = meeting.pop("sections")
        meetings.append({"section": " + ".join(sections), **meeting})
    return {
        "role": "Core" if choice.is_core else "Elective",
        "course": course.course,
        "title": course.title,
        "units": course.units,
        "bundle": option.label,
        "components": option.components or (option.label,),
        "online": option.modality == "online",
        "prerequisites": course.prerequisites,
        "prerequisiteStatus": course.prerequisite_status,
        "unresolved": option.has_unresolved_time,
        "meetings": meetings,
    }


def _export_data(config: FeasibleConfig, schedules: list[FeasibleSchedule]) -> dict:
    choices: list[dict] = []
    choice_indices: dict[tuple, int] = {}
    schedule_data = []
    for schedule in schedules:
        indices = []
        for choice in schedule.choices:
            key = _choice_key(choice)
            if key not in choice_indices:
                choice_indices[key] = len(choices)
                choices.append(_choice_data(choice))
            indices.append(choice_indices[key])
        continuity = schedule_continuity(schedule, config.semester)
        schedule_data.append({
            "choices": indices,
            "electiveUnits": schedule.elective_units,
            "totalUnits": sum(choice.course.units for choice in schedule.choices),
            "unknownTime": schedule.has_unknown_time,
            "prerequisiteAdvisory": schedule.has_prerequisite_advisory,
            "continuity": continuity["minis"],
            "totalGapMinutes": continuity["totalGapMinutes"],
            "maxGapMinutes": continuity["maxGapMinutes"],
        })
    return {
        "minis": SOC_MINIS[config.semester[0]],
        "currentSections": dict(config.current_sections),
        "choices": choices,
        "schedules": schedule_data,
    }


def build_html(config: FeasibleConfig, schedules: list[FeasibleSchedule], snapshot_date: str) -> str:
    data = json.dumps(_export_data(config, schedules), separators=(",", ":")).replace("</", "<\\/")
    template_dir = Path(__file__).parent / "templates"
    script = "\n".join(
        (template_dir / name).read_text(encoding="utf-8")
        for name in ("feasible.js", "feasible_tree.js")
    )
    style = (template_dir / "feasible.css").read_text(encoding="utf-8")
    core = ", ".join(config.core_courses)
    electives = ", ".join(config.elective_courses)
    return (
        "<!doctype html><html><head><meta charset='utf-8'><meta name='viewport' content='width=device-width'>"
        f"<title>Feasible schedules — {config.semester}</title><style>{_suggest_style()}{style}</style></head><body>"
        f"<h1>All feasible schedules — {config.semester}</h1>"
        f"<p class='meta'>Snapshot: {html_lib.escape(snapshot_date)} · Maximum elective units: "
        f"{config.max_elective_units} · Maximum online courses: 1</p>"
        "<p class='online-note'><span class='online-sample'>Sky blue</span> = online.</p>"
        f"<p><strong>Core:</strong> {html_lib.escape(core)}</p>"
        f"<p><strong>Electives:</strong> {html_lib.escape(electives)}</p>"
        f"<p><strong>{len(schedules)} schedule{'s' if len(schedules) != 1 else ''}</strong></p>"
        "<div class='schedule-layout'><nav class='schedule-browser' aria-label='Schedule selection'>"
        "<h2>Schedule tree</h2><p class='meta'>Choose an elective set, then a section combination.</p>"
        "<div class='schedule-filter'><label for='section-filter'>Exact course section</label>"
        "<select id='section-filter'><option value=''>All sections</option></select>"
        "<p id='schedule-filter-status' class='meta' aria-live='polite'></p></div>"
        "<div id='schedule-tree' class='schedule-tree'></div></nav>"
        "<main id='schedule-view' class='schedule-view'></main></div>"
        f"<script id='schedule-data' type='application/json'>{data}</script><script>{script}</script>"
        "</body></html>"
    )
