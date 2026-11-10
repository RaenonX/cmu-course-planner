import html as html_lib
from collections import Counter

from ..common.labels import category_tag_class
from ..common.rating import star_rating
from .models import Course

def _route_count_summary(schedule: list[list[Course]], prefer: list[str]) -> str:
    courses = [course for sem_courses in schedule for course in sem_courses]
    rating_counts = Counter(course.effective_rating(prefer) for course in courses)
    category_counts = Counter(
        category
        for course in courses
        for category in course.category
    )
    parts = [
        f'<span class="tag tag-rating" title="{rating}/5">{star_rating(rating)}: {count}</span>'
        for rating, count in sorted(rating_counts.items(), reverse=True)
    ]
    for category, count in sorted(category_counts.items()):
        parts.append(
            f'<span class="tag {category_tag_class(category)}">'
            f'{html_lib.escape(category)}: {count}</span>'
        )
    return "".join(parts)

def _route_semester_label(sem_courses: list[Course]) -> str:
    if not sem_courses:
        return "No courses"
    return " + ".join(course.course for course in sorted(sem_courses, key=lambda item: item.course))


def _route_section_label(schedule: list[list[Course]]) -> str:
    selected = [course for semester in schedule for course in semester]
    if not selected:
        return "No selected sections"
    return " · ".join(
        html_lib.escape(
            f"{course.course} {course.selected_section or 'Section unknown'}"
            f"{' M' + str(course.selected_mini) if course.selected_mini else ''}"
        )
        for course in selected
    )


def _route_leaf_label(
    route_idx: int,
    schedule: list[list[Course]],
    prefer: list[str],
) -> str:
    return (
        f'<span class="route-tree-route">Route {route_idx + 1}</span>'
        f'<span class="route-section-choice">{_route_section_label(schedule)}</span>'
        f'<span class="route-count-summary">{_route_count_summary(schedule, prefer)}</span>'
    )
