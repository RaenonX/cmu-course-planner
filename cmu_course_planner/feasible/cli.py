import argparse
import sys
from pathlib import Path

from ..common.config import completed_courses_from_config
from ..common.paths import DEFAULT_CONFIG, FEASIBLE_OUTPUT_PATTERN, OUT_DIR
from ..suggest.load import load_config
from .config import parse_feasible_config
from .enumerate import enumerate_schedules
from .load import load_exact_courses
from .render import build_html


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Enumerate every feasible exact-term CMU schedule.")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG, metavar="FILE")
    args = parser.parse_args()
    try:
        raw = load_config(args.config)
        config = parse_feasible_config(raw)
        all_ids = (*config.core_courses, *config.elective_courses)
        courses, snapshot_date = load_exact_courses(
            all_ids, config.semester, completed_courses_from_config(raw)
        )
        by_id = {course.course: course for course in courses}
        schedules = enumerate_schedules(
            [by_id[course_id] for course_id in config.core_courses],
            [by_id[course_id] for course_id in config.elective_courses],
            config.semester,
            config.max_elective_units,
        )
    except ValueError as error:
        raise SystemExit(f"ERROR: {error}") from error
    output = OUT_DIR / FEASIBLE_OUTPUT_PATTERN.format(semester=config.semester)
    OUT_DIR.mkdir(exist_ok=True)
    output.write_text(build_html(config, schedules, snapshot_date), encoding="utf-8")
    print(f"Enumerated {len(schedules)} feasible schedules.")
    print(f"Schedule written → {output}")
