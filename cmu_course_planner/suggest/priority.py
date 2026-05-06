from .models import Course
from .variants import ROUTE_DIVERSITY_WIDTH

def _sort_key(variant: str, prefer: list[str], remaining_soc: set[str]):
    def key(c: Course) -> tuple:
        scarcity = len(c.offered_soc_types() & remaining_soc)
        rating = c.effective_rating(prefer)
        if variant == "Rating First":
            return (-rating, scarcity, c.course)
        return (scarcity, -rating, c.course)
    return key

def _placeable(c: Course, budget: int, taken_minis: set[int], soc_type: str) -> int | None:
    if c.units > budget:
        return None

    offering = c.offering_for(soc_type)
    offering_minis = offering.minis if offering else []

    if offering_minis:
        available = [m for m in offering_minis if m not in taken_minis]
        if not available:
            return None
        return available[0]

    return 0

def _route_choice_index(route_seed: int, semester_idx: int, course_idx: int, candidate_count: int) -> int:
    if route_seed == 0 or candidate_count <= 1:
        return 0
    width = min(ROUTE_DIVERSITY_WIDTH, candidate_count)
    return (route_seed + semester_idx * 3 + course_idx * 5) % width
