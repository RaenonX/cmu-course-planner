from ..common.config import USER_TO_SOC
from .models import Course, Meeting
from .priority import _placeable, _route_choice_index, _sort_key
from .time import _continuity_score

def suggest(
    courses: list[Course],
    semesters: list[str],
    units_max: int,
    prefer: list[str],
    current_time_ranges: list[Meeting],
    variant: str = "Rating First",
    route_seed: int = 0,
) -> tuple[list[list[Course]], list[Course]]:
    """
    Greedy scheduler with per-mini-slot tracking.

    Mini constraint: each mini slot (1-6) may be used at most once per semester.
    Two courses in the same slot (e.g. both M2) are rejected — only consecutive
    slots are permitted (e.g. M1 + M2).

    A course with minis=[1,2] can be placed in either slot 1 or slot 2; the first
    available one is chosen.  A course with minis=[] is full-semester (no slot used).
    """
    assigned: set[str] = set()
    schedule: list[list[Course]] = [[] for _ in semesters]

    for idx, sem in enumerate(semesters):
        soc = USER_TO_SOC[sem]
        remaining_soc = {USER_TO_SOC[s] for s in semesters[idx:]}

        candidates = [
            c for c in courses
            if c.course not in assigned and soc in c.offered_soc_types()
        ]
        candidates.sort(key=_sort_key(variant, prefer, remaining_soc))

        budget = units_max
        taken_minis: set[int] = set()   # mini slot numbers used in this semester

        while candidates:
            if variant == "Time Continuity First":
                semester_time_ranges = current_time_ranges if idx == 0 else []
                base_overlap, base_gap = _continuity_score(schedule[idx], soc, semester_time_ranges)
                ranked = []
                for c in candidates:
                    chosen_slot = _placeable(c, budget, taken_minis, soc)
                    if chosen_slot is None:
                        continue
                    next_overlap, next_gap = _continuity_score([*schedule[idx], c], soc, semester_time_ranges)
                    ranked.append((
                        next_overlap - base_overlap,
                        next_gap - base_gap,
                        *_sort_key("Rating First", prefer, remaining_soc)(c),
                        c,
                        chosen_slot,
                    ))
                if not ranked:
                    break
                ranked.sort(key=lambda item: item[:-2])
                choice_idx = _route_choice_index(route_seed, idx, len(schedule[idx]), len(ranked))
                *_, c, chosen_slot = ranked[choice_idx]
            else:
                ranked = []
                for c in candidates:
                    chosen_slot = _placeable(c, budget, taken_minis, soc)
                    if chosen_slot is not None:
                        ranked.append((c, chosen_slot))
                if not ranked:
                    break
                choice_idx = _route_choice_index(route_seed, idx, len(schedule[idx]), len(ranked))
                c, chosen_slot = ranked[choice_idx]

            candidates = [candidate for candidate in candidates if candidate.course != c.course]

            schedule[idx].append(c)
            assigned.add(c.course)
            budget -= c.units
            if chosen_slot:
                taken_minis.add(chosen_slot)

            if budget == 0:
                break

    unplaced = [c for c in courses if c.course not in assigned]
    return schedule, unplaced
