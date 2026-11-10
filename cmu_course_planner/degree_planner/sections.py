from .models import Course, SectionOption


def section_choices(course: Course, soc_type: str, slots: list[int]) -> list[tuple[int, SectionOption]]:
    offering = course.offering_for(soc_type)
    if not offering:
        return []
    choices = []
    for slot in slots:
        selected_mini = slot or 0
        choices.extend(
            (selected_mini, option)
            for option in offering.section_options
            if option.mini == (slot or None)
        )
    return choices
