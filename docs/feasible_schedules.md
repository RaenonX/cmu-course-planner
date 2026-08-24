# Exhaustive Exact-Semester Schedules

`plan_feasible.py` enumerates every conflict-free registration schedule for the
exact SOC semester configured under `feasible_schedule` in `plan_config.yml`.

## Data flow

1. `export_report.py` refreshes `out/course-snapshot.json` from the CMU SOC.
2. Term-specific policies assemble ambiguous SOC components into complete
   registration bundles, such as `Lec 11 + B1` for 17-614.
3. `plan_feasible.py` selects one complete bundle for every core course and
   zero or one bundle for each elective course, requiring at least one elective
   course in every returned schedule.
4. `out/feasible-schedules-F26.html` lists every feasible result with exact
   sections and separate Mini 1 and Mini 2 timelines.

## Constraints

- Every core course is mandatory.
- Every returned schedule contains at least one elective course.
- Elective-course units alone must not exceed `max_elective_units`.
- A selected course consumes its units once, even when its bundle has multiple
  components.
- Meeting conflicts are day-, time-, and mini-aware. Full-semester meetings
  participate in both minis.
- At most one selected course may use an online bundle; the export renders its
  course code in sky blue.
- Prerequisites are advisory and visibly marked as satisfied, unsatisfied, or
  unknown in the export.
- A TBA or otherwise unresolved meeting is retained with a warning that its
  schedule cannot be fully conflict-verified.

Invalid, unresolvable, and not-offered course codes are fatal. The planner does
not silently omit them.

The export groups schedules as a tree: each branch is a distinct elective-course
set, and its leaves are the feasible complete-section combinations. Tree labels
show elective course codes only; core courses and section details stay in the
selected-schedule view. Selecting a leaf shows the picked course codes, exact
section table, and mini timelines. Clicking a displayed course code opens its
full title in a small popover. The exact-course-section filter keeps only
schedules containing the selected course component, such as `17-623 D2`, even
when that component belongs to a larger complete registration bundle.

Each leaf tooltip and selected-schedule detail panel summarize the occupied time
range and effective gap for grouped weekdays in each mini, plus the total gap
across weekdays and the maximum gap on any single weekday. Effective gaps omit
the first 10 minutes between meetings as transition time. Leaves within an
elective-course branch are sorted by section-swap count, then total effective
gap, both ascending, with the enumerator's stable order as the final tie-breaker.
Each leaf shows only its total and maximum effective gaps and section-swap
count; the selected-schedule detail panel lists the core section swaps relative
to the section and lecture labels in `current_time_ranges`.
Bundle components with identical days and times are coalesced into one timeline
meeting while retaining all of their section labels.

## Commands

```powershell
.venv/Scripts/python export_report.py
.venv/Scripts/python plan_feasible.py
```
