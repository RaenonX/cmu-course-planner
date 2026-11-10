from .models import Course, Meeting
from .scheduler import plan_degree
from .variants import ROUTE_ATTEMPTS

def _schedule_signature(schedule: list[list[Course]], unplaced: list[Course]) -> tuple:
    return (
        tuple(
            tuple((c.course, c.selected_mini, c.selected_section) for c in sem_courses)
            for sem_courses in schedule
        ),
        tuple(c.course for c in unplaced),
    )

def plan_degree_routes(
    courses: list[Course],
    semesters: list[str],
    unit_caps: list[int],
    prefer: list[str],
    current_time_ranges: list[Meeting],
    variant: str,
) -> list[tuple[list[list[Course]], list[Course]]]:
    routes: list[tuple[list[list[Course]], list[Course]]] = []
    seen: set[tuple] = set()

    for route_seed in range(ROUTE_ATTEMPTS):
        schedule, unplaced = plan_degree(
            courses,
            semesters,
            unit_caps,
            prefer,
            current_time_ranges,
            variant,
            route_seed,
        )
        signature = _schedule_signature(schedule, unplaced)
        if signature in seen:
            continue
        routes.append((schedule, unplaced))
        seen.add(signature)
    return routes
