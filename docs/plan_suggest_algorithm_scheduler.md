# Plan Suggester Algorithm: Scheduler Details

## Step 2 — Greedy per-semester scheduler

`suggest(courses, semesters, units_max, prefer)` assigns courses to semesters in order.
`suggest_routes(...)` repeats that scheduler with deterministic route seeds and keeps
unique schedule/unplaced combinations, up to 10 routes per strategy.

### Candidate selection

For semester `sem` (SOC type `soc`), a course is a **candidate** when:

- It has not been assigned in a previous semester.
- It has at least one detected offering with SOC type `soc` (e.g. `"F"` for Fall).

### Candidate sort key

Balanced:
```
(scarcity, -course_preference, -category_preference, course_id)   ascending
```

Preference First:
```
(-course_preference, -category_preference, scarcity, course_id)   ascending
```

No Preference:
```
(scarcity, course_id)   ascending
```

Time Continuity:
```
(incremental_overlap, incremental_gap, scarcity, -course_preference, -category_preference, course_id)   ascending
```

| Key | Value | Effect |
|-----|-------|--------|
| `incremental_overlap` | Added overlapping minutes against current and selected course times in compatible mini slots | Lower = fewer conflicts = placed earlier |
| `incremental_gap` | Added same-day minutes between current and selected course intervals | Lower = tighter time continuity = placed earlier |
| `scarcity` | Number of distinct SOC types (among remaining semesters) that offer this course | Lower = rarer = placed earlier |
| `-course_preference` | `-1` when the course ID is listed in `prefer_courses`, else `0` | Explicit course match = placed earlier |
| `-category_preference` | Negative count of `prefer_categories` entries matched by this course | Higher match = placed earlier |
| `course_id` | Lexicographic course ID string | Stable tiebreak |

**Scarcity** is computed against the remaining semesters from the current one onward, so a course available only in Fall is ranked ahead of one available in both Fall and Spring when scheduling a Fall semester.

### Time continuity

The Time Continuity variant still uses the same greedy placement loop and mini-aware conflict checks, but it re-ranks candidates after each selected course.

For the first planned semester, the current schedule starts with `current_time_ranges` from `plan_config.yml`. Later planned semesters start from an empty current-time set. For every candidate, the scheduler computes:

1. How many additional overlapping minutes the candidate introduces.
2. How many additional same-day gap minutes the candidate introduces between current and selected intervals in compatible mini slots.
3. The normal Balanced sort key as the tiebreaker.

This means a non-overlapping course that sits directly before or after an existing course is preferred over one that creates a large idle gap. If two candidates have the same continuity score, the Balanced priority rules decide the order.

### Greedy fill

Iterate sorted candidates and assign the course to this semester when all three hold:

1. `course.units ≤ remaining_budget`
2. The selected section does not introduce overlapping minutes against current ranges or already selected courses in the same semester.
3. *(implicit)* Course not already assigned

Update state on assignment:
- `budget -= course.units`
- Add course to `assigned` set

Stop early when `budget == 0`.

Route 1 uses the top-ranked placeable course at each decision point. Later routes
choose from the top few placeable candidates using a deterministic seed. This keeps
each strategy's priority rules in control while producing alternate viable routes
instead of only one greedy result.

### Mini constraint

Each mini course is evaluated per concrete mini section. A course with `minis=[1, 2]` is considered once for mini-1 and once for mini-2. The scheduler records the chosen slot and uses only meeting rows from that slot when computing continuity and rendering the final route. Full-semester courses have `minis=[]` and are compared against all mini slots in that semester.

`current_time_ranges` entries can also provide `mini: 1` through `mini: 6`. Mini-specific current ranges only conflict with full-semester courses or courses in the same mini slot, so a mini-1 course and a mini-2 course may share the same lecture clock time.

## Step 3 — Unplaced courses

Any course not in `assigned` after all semesters are processed is collected into `unplaced`. These appear in the console output and in the "Not placed" section of the HTML report, with all detected offering semesters shown as clickable chips.

## Output

- **Console** — semester-by-semester listing for route 1 of the primary strategy, with units, mini labels, and enr-apps links.
- **`out/suggested-schedule.html`** — each strategy tab contains up to 10 distinct routes, rendered as styled HTML tables with clickable course links.
