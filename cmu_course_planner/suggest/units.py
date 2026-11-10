from .models import Course
from .time import SOC_MINIS


def mini_workloads(items: list[tuple[int, int | None]], soc_type: str) -> dict[int, int]:
    """Nominal weekly hours: full-term units plus twice each active mini's units."""
    return {
        mini: sum(units if selected_mini is None else 2 * units
                  for units, selected_mini in items
                  if selected_mini is None or selected_mini == mini)
        for mini in SOC_MINIS[soc_type]
    }


def semester_unit_total(courses: list[Course]) -> int:
    return sum(course.units for course in courses)


def candidate_slots(
    course: Course,
    unit_cap: int,
    soc_type: str,
    selected_courses: list[Course],
) -> list[int]:
    if semester_unit_total(selected_courses) + course.units > unit_cap:
        return []

    offering = course.offering_for(soc_type)
    offering_minis = offering.minis if offering else []
    selected = [(item.units, item.selected_mini) for item in selected_courses]
    return [
        slot for slot in (offering_minis or [0])
        if max(mini_workloads([*selected, (course.units, slot or None)], soc_type).values()) <= unit_cap
    ]
