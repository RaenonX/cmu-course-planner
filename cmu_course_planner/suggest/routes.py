from .models import Course, Meeting
from .scheduler import suggest
from .variants import ROUTE_ATTEMPTS, ROUTES_PER_VARIANT

def _schedule_signature(schedule: list[list[Course]], unplaced: list[Course]) -> tuple:
    return (
        tuple(tuple(c.course for c in sem_courses) for sem_courses in schedule),
        tuple(c.course for c in unplaced),
    )

def suggest_routes(
    courses: list[Course],
    semesters: list[str],
    units_max: int,
    prefer: list[str],
    current_time_ranges: list[Meeting],
    variant: str,
    route_count: int = ROUTES_PER_VARIANT,
) -> list[tuple[list[list[Course]], list[Course]]]:
    routes: list[tuple[list[list[Course]], list[Course]]] = []
    seen: set[tuple] = set()

    for route_seed in range(ROUTE_ATTEMPTS):
        schedule, unplaced = suggest(
            courses,
            semesters,
            units_max,
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
        if len(routes) >= route_count:
            break

    return routes
