from .models import Course


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
    if offering_minis:
        occupied_minis = {
            selected.selected_mini
            for selected in selected_courses
            if selected.selected_mini is not None
        }
        return [mini for mini in offering_minis if mini not in occupied_minis]
    return [0]
