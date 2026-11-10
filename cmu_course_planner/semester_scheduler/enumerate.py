from ..degree_planner.time import _meeting_buckets, _meeting_days, _meeting_interval
from ..degree_planner.units import mini_workloads
from .models import CourseChoice, SemesterSchedule


MAX_ONLINE_COURSES = 1


def _conflicts(candidate: CourseChoice, selected: list[CourseChoice], soc_type: str) -> bool:
    for candidate_meeting in candidate.option.meetings:
        candidate_interval = _meeting_interval(candidate_meeting)
        if candidate_interval is None:
            continue
        candidate_days = set(_meeting_days(candidate_meeting.days))
        candidate_minis = set(_meeting_buckets(candidate_meeting, soc_type))
        for choice in selected:
            for meeting in choice.option.meetings:
                interval = _meeting_interval(meeting)
                if interval is None:
                    continue
                if not candidate_days.intersection(_meeting_days(meeting.days)):
                    continue
                if not candidate_minis.intersection(_meeting_buckets(meeting, soc_type)):
                    continue
                if candidate_interval[0] < interval[1] and interval[0] < candidate_interval[1]:
                    return True
    return False


def enumerate_schedules(core, electives, semester: str, max_elective_units: int) -> list[SemesterSchedule]:
    items = [(course, True) for course in core] + [(course, False) for course in electives]
    soc_type = semester[0]
    # The elective allowance plus mandatory units defines the total planning cap.
    unit_cap = sum(course.units for course in core) + max_elective_units
    results: list[SemesterSchedule] = []

    def visit(index: int, selected: list[CourseChoice], elective_units: int, online_count: int) -> None:
        if index == len(items):
            if elective_units == 0:
                return
            choices = tuple(sorted(selected, key=lambda choice: choice.course.course))
            results.append(SemesterSchedule(choices, elective_units))
            return
        course, is_core = items[index]
        if not is_core:
            visit(index + 1, selected, elective_units, online_count)
            if elective_units + course.units > max_elective_units:
                return
        offering = course.offering_for_semester(semester)
        assert offering is not None
        for option in offering.section_options:
            next_online = online_count + (option.modality == "online")
            if next_online > MAX_ONLINE_COURSES:
                continue
            choice = CourseChoice(course, option, is_core)
            workload = mini_workloads(
                [(item.course.units, item.option.mini) for item in [*selected, choice]],
                soc_type,
            )
            if max(workload.values()) > unit_cap:
                continue
            if _conflicts(choice, selected, soc_type):
                continue
            visit(
                index + 1,
                [*selected, choice],
                elective_units + (0 if is_core else course.units),
                next_online,
            )

    visit(0, [], 0, 0)
    results.sort(key=lambda result: (
        -result.elective_units,
        -sum(not choice.is_core for choice in result.choices),
        tuple((choice.course.course, choice.option.label) for choice in result.choices),
    ))
    return results
