from random import Random

from .models import Course

def _sort_key(variant: str, prefer: list[str], remaining_soc: set[str]):
    def key(c: Course) -> tuple:
        scarcity = len(c.offered_soc_types() & remaining_soc)
        rating = c.effective_rating(prefer)
        if variant == "Rating First":
            return (-rating, scarcity, c.course)
        return (scarcity, -rating, c.course)
    return key

def _route_choice_index(route_seed: int, semester_idx: int, course_idx: int, candidate_count: int) -> int:
    if route_seed == 0 or candidate_count <= 1:
        return 0
    # Independently sample each decision, reproducibly. Modular rotation ties
    # choices together and repeats routes instead of exploring combinations.
    return Random(f"{route_seed}:{semester_idx}:{course_idx}").randrange(candidate_count)
