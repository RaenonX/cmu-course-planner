from dataclasses import replace

from ..common.config import SEM_LABEL, USER_TO_SOC
from .models import Course, Meeting
from .sections import section_choices
from .time import _continuity_score, _selected_section_option, course_time_conflicts
from .units import candidate_slots, semester_unit_total


def _warnings(course: Course, selected: Course | None, soc_type: str) -> list[str]:
    warnings = []
    if course.prerequisite_status == "unsatisfied":
        warnings.append(f"Prerequisite is marked unsatisfied: {course.prerequisites}.")
    elif course.prerequisite_status == "unknown":
        warnings.append(f"Prerequisite eligibility could not be determined: {course.prerequisites}.")
    option = _selected_section_option(selected, soc_type) if selected else None
    if option and option.has_unresolved_time:
        warnings.append("The selected section has TBA or incomplete meeting-time data.")
    return warnings


def analyze_swap(
    course: Course,
    soc_type: str,
    semester_courses: list[Course],
    units_max: int,
    current_time_ranges: list[Meeting],
    removed_course: Course | None,
) -> dict:
    remaining = [c for c in semester_courses if c is not removed_course]
    removed_units = removed_course.units if removed_course else 0
    total = semester_unit_total(remaining) + course.units
    base = {
        "remove": removed_course.course if removed_course else "",
        "removeLabel": (
            f"Remove {removed_course.course} — {removed_course.title}"
            if removed_course else "Keep all scheduled courses"
        ),
        "unitsAfter": total,
    }
    if not course.offering_for(soc_type):
        return {
            **base,
            "status": "rejected",
            "summary": "No detected offering",
            "reasons": ["This course has no detected offering for this semester type."],
            "warnings": _warnings(course, None, soc_type),
        }

    slots = candidate_slots(course, units_max, soc_type, remaining)
    reasons = []
    if total > units_max:
        reasons.append(
            f"Unit limit exceeded: {total}/{units_max} units after "
            f"removing {removed_units} and adding {course.units}."
        )
    offering = course.offering_for(soc_type)
    occupied = {
        selected.selected_mini: selected.course
        for selected in remaining
        if selected.selected_mini is not None
    }
    if offering and offering.minis and not any(mini not in occupied for mini in offering.minis):
        blockers = ", ".join(f"Mini {mini} by {occupied[mini]}" for mini in offering.minis)
        reasons.append(f"Every offered mini slot is occupied ({blockers}).")

    choices = section_choices(course, soc_type, slots)
    base_overlap, _ = _continuity_score(remaining, soc_type, current_time_ranges)
    rejected_sections = []
    for chosen_slot, option in choices:
        selected = replace(
            course,
            selected_mini=chosen_slot or None,
            selected_section=option.label,
        )
        next_overlap, _ = _continuity_score(
            [*remaining, selected], soc_type, current_time_ranges
        )
        if next_overlap == base_overlap:
            mini = f", Mini {chosen_slot}" if chosen_slot else ""
            return {
                **base,
                "status": "works",
                "summary": f"{total}/{units_max} units · Section {option.label}{mini}",
                "reasons": [],
                "warnings": _warnings(course, selected, soc_type),
            }
        conflicts = course_time_conflicts(
            selected, soc_type, remaining, current_time_ranges
        )
        label = f"Section {option.label}"
        if chosen_slot:
            label += f" (Mini {chosen_slot})"
        rejected_sections.append(f"{label}: conflicts with {', '.join(conflicts)}.")

    if not reasons:
        reasons.extend(rejected_sections or ["No usable section schedule was detected."])
    return {
        **base,
        "status": "rejected",
        "summary": "The selected replacement does not fit",
        "reasons": reasons,
        "warnings": _warnings(course, None, soc_type),
    }


def build_what_if_data(
    semesters: list[str],
    schedule: list[list[Course]],
    unplaced: list[Course],
    units_max: int,
    current_time_ranges: list[Meeting],
) -> dict:
    courses = []
    for course in unplaced:
        semester_results = []
        for index, sem in enumerate(semesters):
            semester_courses = schedule[index]
            current = current_time_ranges if index == 0 else []
            swaps = [
                analyze_swap(course, USER_TO_SOC[sem], semester_courses, units_max, current, None)
            ]
            swaps.extend(
                analyze_swap(course, USER_TO_SOC[sem], semester_courses, units_max, current, removed)
                for removed in semester_courses
            )
            semester_results.append({
                "index": index,
                "label": f"Semester {index + 1} · {SEM_LABEL[sem]}",
                "offered": course.offering_for(USER_TO_SOC[sem]) is not None,
                "swaps": swaps,
            })
        courses.append({
            "id": course.course,
            "label": f"{course.course} — {course.title}",
            "semesters": semester_results,
        })
    return {"courses": courses, "unitsMax": units_max}
