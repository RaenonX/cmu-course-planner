from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PLAN_CONFIG = ROOT / "plan_config.yml"
DEFAULT_CONFIG = PLAN_CONFIG
OUT_DIR = ROOT / "out"
REPORT_OUTPUT = OUT_DIR / "course-report.html"
SNAPSHOT = OUT_DIR / "course-snapshot.json"
SUGGEST_OUTPUT = OUT_DIR / "suggested-schedule.html"
PACKAGE_DIR = Path(__file__).resolve().parents[1]
REPORT_TEMPLATE_DIR = PACKAGE_DIR / "report" / "templates"
SUGGEST_TEMPLATE_DIR = PACKAGE_DIR / "suggest" / "templates"
