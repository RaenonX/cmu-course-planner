from dataclasses import replace

from ..common.config import SEM_LABEL, USER_TO_SOC
from .models import Meeting
from .semester_render import _semester_heading
from .tables import TABLE_HEAD, _course_row, _unplaced_row
from .time import SOC_MINIS, _meeting_days, _meeting_interval
from .what_if_render import what_if_panel


def meeting_data(meeting: Meeting) -> dict:
    interval = _meeting_interval(meeting)
    return {"days": _meeting_days(meeting.days), "begin": interval[0] if interval else None,
            "end": interval[1] if interval else None, "mini": meeting.mini,
            "label": meeting.label or "Current commitment", "section": meeting.section,
            "text": f"{meeting.days} {meeting.begin}–{meeting.end}"}


def build_path_data(courses, semesters, unit_caps, prefer, current) -> dict:
    terms = []
    for index, semester in enumerate(semesters):
        soc = USER_TO_SOC[semester]
        options = []
        for course in courses:
            offering = course.offering_for(soc)
            options.append([{
                "label": option.label, "mini": option.mini,
                "unresolved": option.has_unresolved_time,
                "meetings": [meeting_data(m) for m in option.meetings],
                "row": _course_row(replace(course, selected_mini=option.mini,
                                           selected_section=option.label), soc, prefer),
            } for option in offering.section_options] if offering else [])
        terms.append({
            "label": f"Semester {index + 1} · {SEM_LABEL[semester]}",
            "minis": SOC_MINIS[soc], "cap": unit_caps[index], "options": options,
            "slots": [(c.offering_for(soc).minis or [None]) if c.offering_for(soc) else []
                      for c in courses],
            "current": [meeting_data(m) for m in current] if index == 0 else [],
            "heading": _semester_heading(index, semester, 0, unit_caps[index], courses),
        })
    return {
        "terms": terms,
        "unitCaps": unit_caps,
        "tableHead": TABLE_HEAD,
        "courses": [{"id": c.course, "label": f"{c.course} — {c.title}", "title": c.title,
                     "mask": str(1 << i), "fixed": c.fixed_semester, "units": c.units,
                     "rating": c.effective_rating(prefer), "categories": c.category,
                     "prerequisites": c.prerequisites, "prerequisiteStatus": c.prerequisite_status,
                     "row": _unplaced_row(c, prefer, "degree-what-if")}
                    for i, c in enumerate(courses)],
        "unplacedHead": TABLE_HEAD.replace("</tr>", "<th>What if?</th></tr>"),
        "whatIfPanel": what_if_panel(),
    }
