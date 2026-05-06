import argparse
from datetime import datetime

from .workflow import export_report


def main() -> None:
    parser = argparse.ArgumentParser(description="Export CMU course report.")
    parser.add_argument(
        "--years", type=int, default=1, metavar="N",
        help="academic years back to check (default: 1)",
    )
    args = parser.parse_args()
    export_report(datetime.now(), args.years)
