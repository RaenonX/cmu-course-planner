import argparse
import sys
from pathlib import Path

from ..common.paths import DEFAULT_CONFIG, OUT_DIR, SUGGEST_OUTPUT
from ..common.config import completed_courses_from_config
from .console import print_primary_route
from .load import load_config, load_current_time_ranges, load_snapshot
from .render import build_html
from .routes import suggest_routes
from .variants import ROUTES_PER_VARIANT, VARIANTS

def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Generate suggested CMU course schedules.")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG, metavar="FILE",
                        help=f"config file (default: {DEFAULT_CONFIG.name})")
    args = parser.parse_args()

    cfg = load_config(args.config)
    semesters: list[str] = cfg.get("semesters", ["F", "S"])
    units_max: int = cfg.get("units_per_semester", 12)
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

    results = []
    for variant_name, variant_desc in VARIANTS:
        routes = suggest_routes(
            courses,
            semesters,
            units_max,
            prefer,
            current_time_ranges,
            variant_name,
        )
        results.append((variant_name, variant_desc, routes))

    print_primary_route(
        semesters, units_max, prefer,
        teaching_location, current_time_ranges, results,
    )

    print(f"Generating {len(VARIANTS)} schedule tabs with up to {ROUTES_PER_VARIANT} routes each…")

    html = build_html(
        semesters,
        results,
        units_max,
        prefer,
        teaching_location,
        snapshot_date,
        courses,
        current_time_ranges,
    )
    OUT_DIR.mkdir(exist_ok=True)
    SUGGEST_OUTPUT.write_text(html, encoding="utf-8")
    print(f"Schedule written → {SUGGEST_OUTPUT}")
