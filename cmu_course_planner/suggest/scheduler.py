from dataclasses import replace

from ..common.config import USER_TO_SOC
from .models import Course, Meeting
from .priority import _route_choice_index, _sort_key
from .sections import section_choices
from .time import _continuity_score
from .units import candidate_slots

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
    Greedy scheduler with a semester unit budget and one course per mini slot.

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

        semester_time_ranges = current_time_ranges if idx == 0 else []

        while candidates:
            base_overlap, base_gap = _continuity_score(schedule[idx], soc, semester_time_ranges)
            if variant == "Time Continuity First":
                ranked = []
                for c in candidates:
                    slots = candidate_slots(c, units_max, soc, schedule[idx])
                    for chosen_slot, option in section_choices(c, soc, slots):
                        selected = replace(
                            c,
                            selected_mini=chosen_slot or None,
                            selected_section=option.label,
                        )
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
                            option.label,
                        ))
                if not ranked:
                    break
                ranked.sort(key=lambda item: item[:-3])
                choice_idx = _route_choice_index(route_seed, idx, len(schedule[idx]), len(ranked))
                *_, c, chosen_slot, chosen_section = ranked[choice_idx]
            else:
                ranked = []
                for c in candidates:
                    slots = candidate_slots(c, units_max, soc, schedule[idx])
                    for chosen_slot, option in section_choices(c, soc, slots):
                        selected = replace(
                            c,
                            selected_mini=chosen_slot or None,
                            selected_section=option.label,
                        )
                        next_overlap, _ = _continuity_score([*schedule[idx], selected], soc, semester_time_ranges)
                        if next_overlap == base_overlap:
                            ranked.append((c, chosen_slot, option.label))
                if not ranked:
                    break
                choice_idx = _route_choice_index(route_seed, idx, len(schedule[idx]), len(ranked))
                c, chosen_slot, chosen_section = ranked[choice_idx]

            candidates = [candidate for candidate in candidates if candidate.course != c.course]

            schedule[idx].append(replace(
                c,
                selected_mini=chosen_slot or None,
                selected_section=chosen_section,
            ))
            assigned.add(c.course)

    unplaced = [c for c in courses if c.course not in assigned]
    return schedule, unplaced
