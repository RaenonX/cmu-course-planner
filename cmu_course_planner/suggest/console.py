from ..common.config import SEM_LABEL, USER_TO_SOC
from ..common.rating import star_rating
from .render_common import _meeting_label, _mini_label

def print_primary_route(semesters, units_max, prefer, teaching_location, current_time_ranges, results) -> None:
    primary_name, _, primary_routes = results[0]
    primary_sched, primary_unplaced = primary_routes[0]
    print(f"=== Suggested Schedule — {primary_name} ===")
    print(f"  Units/semester : {units_max}")
    print(f"  Semesters      : {' → '.join(SEM_LABEL[s] for s in semesters)}")
    print(f"  Teaching loc.  : {teaching_location}")
    print(f"  Current times  : {len(current_time_ranges)} range(s)")
    print(f"  Categories     : {', '.join(prefer) if prefer else 'none'}")
    print()
    for idx, sem in enumerate(semesters):
        soc = USER_TO_SOC[sem]
        sem_courses = primary_sched[idx]
        total = sum(c.units for c in sem_courses)
        print(f"Semester {idx + 1} — {SEM_LABEL[sem]}  ({total}/{units_max} units)")
        for c in sem_courses:
            cats = f"  [{', '.join(c.category)}]" if c.category else ""
            rating = f"  [{star_rating(c.effective_rating(prefer))}]"
            offering = c.offering_for(soc)
            minis = offering.minis if offering else []
            mini_str = f"  {_mini_label(minis)}" if minis else ""
            time_str = ""
            if offering and offering.meetings:
                time_str = "  " + ", ".join(_meeting_label(m) for m in offering.meetings)
            link = c.last_link_for(soc) or ""
            print(f"  {c.course}  {c.title} ({c.units}u){rating}{cats}{mini_str}{time_str}")
            if link:
                print(f"    {link}")
        if not sem_courses:
            print("  (no courses)")
        print()

    if primary_unplaced:
        print("Not placed:")
        for c in primary_unplaced:
            offered = ", ".join(o.semester for o in c.offered_in) if c.offered_in else "none"
            print(f"  {c.course}  {c.title}  [offered: {offered}]")
        print()
