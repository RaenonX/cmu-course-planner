from .models import Course
from .time import SOC_MINIS


def semester_unit_loads(courses: list[Course], soc_type: str) -> dict[int, int]:
    """Concurrent suggested-course units in each mini slot of a semester."""
    loads = {mini: 0 for mini in SOC_MINIS[soc_type]}
    for course in courses:
        if course.selected_mini is not None:
            loads[course.selected_mini] += course.units
            continue
        for mini in loads:
            loads[mini] += course.units
    return loads


def candidate_slots(
    course: Course,
    unit_cap: int,
    soc_type: str,
    loads: dict[int, int],
) -> list[int]:
    offering = course.offering_for(soc_type)
    offering_minis = offering.minis if offering else []
    if offering_minis:
        return [mini for mini in offering_minis if loads[mini] + course.units <= unit_cap]
    if all(load + course.units <= unit_cap for load in loads.values()):
        return [0]
    return []
