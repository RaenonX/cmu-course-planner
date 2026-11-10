from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PLAN_CONFIG = ROOT / "plan_config.yml"
DEFAULT_CONFIG = PLAN_CONFIG
OUT_DIR = ROOT / "out"
REPORT_OUTPUT = OUT_DIR / "course-report.html"
SNAPSHOT = OUT_DIR / "course-snapshot.json"
DEGREE_PLANNER_OUTPUT = OUT_DIR / "degree-planner.html"
SEMESTER_SCHEDULER_OUTPUT_PATTERN = "semester-scheduler-{semester}.html"
PACKAGE_DIR = Path(__file__).resolve().parents[1]
REPORT_TEMPLATE_DIR = PACKAGE_DIR / "report" / "templates"
DEGREE_PLANNER_TEMPLATE_DIR = PACKAGE_DIR / "degree_planner" / "templates"
SECTION_POLICIES = PACKAGE_DIR / "report" / "section_policies.yml"
