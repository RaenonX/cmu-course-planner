import argparse
import sys
from pathlib import Path

from ..common.paths import DEFAULT_CONFIG, OUT_DIR, DEGREE_PLANNER_OUTPUT
from ..common.config import completed_courses_from_config
from .load import load_config, load_current_time_ranges, load_snapshot
from .render import build_html

def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="CMU Degree Planner: plan courses across semesters.")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG, metavar="FILE",
                        help=f"config file (default: {DEFAULT_CONFIG.name})")
    args = parser.parse_args()

    cfg = load_config(args.config)
    semesters: list[str] = cfg.get("semesters", ["F", "S"])
    unit_caps: list[int] = cfg["units_per_semester"]
    prefer: list[str] = cfg.get("prefer_categories") or []
    require: bool = cfg.get("require_categories", False)
    teaching_location: str = cfg["teaching_location"]
    current_time_ranges = load_current_time_ranges(cfg)
    config_courses: list[dict] = cfg.get("courses", [])
    completed_courses = completed_courses_from_config(cfg)

    courses, snapshot_date = load_snapshot(
        config_courses,
        prefer,
        require,
        teaching_location,
        completed_courses,
    )

    print("Building the report with exhaustive browser-side path generation…", flush=True)

    html = build_html(
        courses,
        semesters,
        unit_caps,
        prefer,
        teaching_location,
        snapshot_date,
        current_time_ranges,
    )
    OUT_DIR.mkdir(exist_ok=True)
    DEGREE_PLANNER_OUTPUT.write_text(html, encoding="utf-8")
    print(f"Degree Planner written → {DEGREE_PLANNER_OUTPUT}")
