# Plan Suggester Algorithm

## Inputs

| Source | Fields used |
|--------|-------------|
| `plan_config.yml` | `semesters`, `units_per_semester`, `teaching_location`, `prefer_categories`, `prefer_courses`, `require_categories`, `current_time_ranges`, course list (IDs + categories) |
| `out/course-snapshot.json` | `teaching_location`, `title`, `units`, `prerequisites`, `offered_in` per course |

## Pipeline

```
load_config  ──►  config_course_ids (set)
                  preferred_course_ids (set)
                  prefer, require, semesters, units_max, teaching_location
                  current_time_ranges

load_snapshot ──► courses[]   (built from config_course_ids;
                               errors if any configured course is missing
                               from the snapshot;
                               matching snapshot teaching_location;
                               category and prerequisites from snapshot,
                               populated by export_report)

suggest_routes ─► route[] = (schedule[][], unplaced[])
```

## Step 1 — Load & filter

`load_snapshot` indexes the snapshot JSON by course ID, then plans from the
`courses` list in `plan_config.yml`. It raises an error when a configured course
is missing from `out/course-snapshot.json`, because that means the snapshot is
stale or the course could not be resolved by `export_report.py`.

Configured courses are kept only when:

1. Its course ID exists in the snapshot.
2. *(if `require_categories: true`)* At least one of its categories matches a `prefer_categories` entry.

Category values come from `export_report.py`, which reads them from `plan_config.yml` and writes them into the snapshot.

`teaching_location` is currently limited to `Pittsburgh, Pennsylvania`. `export_report.py` uses it when detecting course offerings, and `plan_suggest.py` rejects snapshots generated for a different or missing location.

`prefer_courses` is read as an explicit set of course IDs. It does not filter the snapshot; it marks matching courses as preferred for preference-aware schedule variants.

`current_time_ranges` is optional and is used to reject first-semester schedule conflicts in all variants. The **Time Continuity** variant also uses it to prefer smaller same-day gaps. Each item has:

```
days: "M W"
begin: "11:00AM"
end: "12:20PM"
mini: 1  # optional; use 1-6 for mini-semester-only ranges
```

Day values may use spaced forms like `M W` / `T Th`, SOC-style compact forms like `MW` / `TR`, or single-day values like `Th` / `F`.
When `mini` is present, that current range is compared only with full-semester
meetings and meetings in the same mini slot. Mini numbering follows CMU SOC
section suffixes: fall uses mini 1/2, spring uses 3/4, and summer uses 5/6.

Prerequisites are read from the SOC course detail page by `export_report.py` and written into `out/course-snapshot.json` as `prerequisites`. HTML reports render this value behind a small clickable `i` control so table rows stay compact until prerequisites are needed.


Scheduler details continue in [plan_suggest_algorithm_scheduler.md](plan_suggest_algorithm_scheduler.md).
