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

def _route_semester_titles(sem_courses: list[Course]) -> str:
    if not sem_courses:
        return '<span class="route-course-title">No courses</span>'
    return "".join(
        f'<span class="route-course-title">{html_lib.escape(f"{course.course} {course.title}")}</span>'
        for course in sem_courses
    )

def _route_tab_label(schedule: list[list[Course]], prefer: list[str]) -> str:
    semester_count = len(schedule)
    parts = [
        f'<span class="route-tab-summary" style="--semester-count:{semester_count}">'
    ]
    for idx, sem_courses in enumerate(schedule):
        cls = "route-sem-dark" if idx % 2 == 0 else "route-sem-gray"
        parts.append(
            f'<span class="route-sem {cls}">{_route_semester_titles(sem_courses)}</span>'
        )
    parts.append(
        f'<span class="route-count-summary">{_route_count_summary(schedule, prefer)}</span>'
    )
    parts.append("</span>")
    return "".join(parts)
