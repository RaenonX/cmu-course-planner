# Degree Planner: Exhaustive Browser Search

## Report generation

`degree_planner.py` validates the configuration, loads the course snapshot, and
exports one self-contained HTML file. It embeds course units, ratings, fixed
semesters, permitted mini slots, section alternatives, normalized meeting times,
and reusable course-table rows. Python does not generate degree paths or
pre-render individual schedules. Opening the HTML starts a Web Worker; no web
server or Node installation is needed to use the report.

## Complete search

`planner_search.js` visits each course once per planned semester:

- Fixed courses must be selected in their configured semester and cannot appear
  in other semesters. Every compatible fixed-course section is explored.
- Each elective may be skipped or selected with any compatible section.
- A selection must fit total semester units and both mini workload limits.
  Full-semester units count in both halves; a mini course contributes twice its
  units in its active half.
- Section mini slots must agree with the detected offering's permitted slots.
- Selected meetings must not add overlaps against other selected courses or
  first-semester current commitments. Meetings in different minis may share the
  same clock time. Missing/TBA times remain advisory uncertainty.

The worker retains each unique semester course/section selection once. Course
sets form shared tree branches, and complete paths join semester selections only
when their course sets are disjoint. This represents the entire Cartesian product
of compatible semester choices without storing millions of duplicated schedules.
Course order does not create additional paths; distinct registration sections do.

The search includes lighter schedules, postponed electives, and empty elective
selections. It has no randomness, seed count, candidate-width limit, or route cap.
If required courses cannot coexist, the report displays the blocking semester.

## Counts, filters, and display

`countPaths` counts compatible continuations using memoized semester/assigned-
course states. Counts use JavaScript `BigInt`. Elective Required/Excluded filters
are applied to the complete path, with exact counts recalculated in the worker.
Preferences never exclude a path merely because it was not sampled.

The browser builds tree nodes only as branches are opened. At a complete
semester course-set path, section combinations are displayed in pages of 100.
Pagination changes only the visible list; every section combination remains
reachable. Selecting a path builds its schedule tables and timeline from the
shared course data. Required courses remain visible in the full schedule, while
tree titles and section labels list electives only.

Both ranking tabs contain the same complete path set:

- **Rating First:** descending counts of five-star electives, then four-star,
  down through one-star; smaller same-day gaps break ties.
- **Time Continuity First:** more elective units, then smaller same-day gaps,
  then the rating counts above.

Ranking is applied semester by semester. Course IDs and selected sections provide
stable final tie-breaks. Changing the ranking never changes feasibility.

## What if?

`planner_what_if.js` runs in the same worker and uses `planner_constraints.js`,
which also supplies the exhaustive search's unit, mini, and time checks. For each
unplaced course it evaluates keeping the schedule or removing one elective.
Fixed courses cannot be removed. Rejections name the unit/workload constraint or
conflicting meetings; prerequisites and unresolved times appear as warnings.
Only the selected path's analysis is calculated.

## Verification

Run `.venv/Scripts/python -m unittest discover -s tests` from the repository.
The Python course fixtures call the actual browser JavaScript through Node for
search and swap tests. Node is required for these development tests, not report
creation or viewing. An independent brute-force fixture checks every assignment,
including deferred/omitted courses and section alternatives. Other regressions
cover fixed-course backtracking, mini limits, conflicts, more than 200 paths,
input-order independence, exact filtering, and swap behavior.
