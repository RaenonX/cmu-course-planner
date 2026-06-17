from dataclasses import replace

from ..common.config import USER_TO_SOC
from .models import Course, Meeting
from .priority import _candidate_slots, _occupied_mini_slots, _route_choice_index, _sort_key
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

    Mini-aware conflict handling:
    A course with minis=[1,2] can be placed in either slot 1 or slot 2.  A course
    with minis=[] is full-semester.  Meetings in different mini slots may share
    the same clock time; meetings in the same mini slot may not overlap.
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
        semester_time_ranges = current_time_ranges if idx == 0 else []

        while candidates:
            base_overlap, base_gap = _continuity_score(schedule[idx], soc, semester_time_ranges)
            occupied_minis = _occupied_mini_slots(schedule[idx])
            if variant == "Time Continuity First":
                ranked = []
                for c in candidates:
                    for chosen_slot in _candidate_slots(c, budget, soc, occupied_minis):
                        selected = replace(c, selected_mini=chosen_slot or None)
                        next_overlap, next_gap = _continuity_score([*schedule[idx], selected], soc, semester_time_ranges)
                        incremental_overlap = next_overlap - base_overlap
                        if incremental_overlap:
                            continue
                        ranked.append((
                            incremental_overlap,
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
                    for chosen_slot in _candidate_slots(c, budget, soc, occupied_minis):
                        selected = replace(c, selected_mini=chosen_slot or None)
                        next_overlap, _ = _continuity_score([*schedule[idx], selected], soc, semester_time_ranges)
                        if next_overlap == base_overlap:
                            ranked.append((c, chosen_slot))
                if not ranked:
                    break
                choice_idx = _route_choice_index(route_seed, idx, len(schedule[idx]), len(ranked))
                c, chosen_slot = ranked[choice_idx]

            candidates = [candidate for candidate in candidates if candidate.course != c.course]

            schedule[idx].append(replace(c, selected_mini=chosen_slot or None))
            assigned.add(c.course)
            budget -= c.units

            if budget == 0:
                break

    unplaced = [c for c in courses if c.course not in assigned]
    return schedule, unplaced
