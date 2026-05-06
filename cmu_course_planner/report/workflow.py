import json
from concurrent.futures import ThreadPoolExecutor, as_completed

import yaml

from ..common.config import validate_teaching_location
from ..common.paths import OUT_DIR, PLAN_CONFIG, REPORT_OUTPUT, SNAPSHOT
from ..common.rating import parse_rating
from .course_parse import _parse_course_info, _parse_prerequisites
from .render import build_report_html, build_report_rows
from .soc import available_semesters, enr_link, fetch, fetch_offering, filter_semesters


def probe_offerings(entries: list[dict], semesters: list[str], teaching_location: str) -> dict:
    pairs = [(e["course"], sem) for e in entries for sem in semesters]
    print(f"Probing {len(pairs)} course×semester combinations...")
    print(f"Teaching location: {teaching_location}")
    results: dict[tuple[str, str], dict | None] = {}
    with ThreadPoolExecutor(max_workers=10) as pool:
        futures = {pool.submit(fetch_offering, cid, sem, teaching_location): (cid, sem) for cid, sem in pairs}
        done = 0
        for fut in as_completed(futures):
            cid, sem = futures[fut]
            results[(cid, sem)] = fut.result()
            done += 1
            print(f"  {done}/{len(pairs)}", end="\r")
    print()
    return results


def resolve_course_info(entries: list[dict], semesters: list[str], results: dict) -> dict[str, tuple[str, int, str]]:
    course_info: dict[str, tuple[str, int, str]] = {}
    for entry in entries:
        cid = entry["course"]
        htmls = [results[(cid, sem)]["html"] for sem in semesters if results.get((cid, sem))]
        if not htmls and semesters:
            _, fallback = fetch(enr_link(cid, semesters[0]))
            if fallback:
                htmls = [fallback]
        if not htmls:
            print(f"  WARNING: {cid} could not be resolved in SOC; skipping report and snapshot.")
            continue
        parsed = [_parse_course_info(h) for h in htmls]
        title = next((t for t, _ in parsed if t != "Unknown"), parsed[0][0])
        unit_values = [u for _, u in parsed if u > 0]
        unique_units = sorted(set(unit_values))
        if len(unique_units) > 1:
            print(f"  WARNING: {cid} has inconsistent unit counts across semesters: {unique_units} - using max ({max(unique_units)})")
        units = max(unit_values) if unit_values else 0
        prerequisites = next((p for p in (_parse_prerequisites(h) for h in htmls) if p != "Unknown"), "Unknown")
        if title == "Unknown" and units == 0:
            print(f"  WARNING: {cid} could not be resolved in SOC; skipping report and snapshot.")
            continue
        course_info[cid] = (title, units, prerequisites)
    return course_info


def build_snapshot(today, semesters: list[str], teaching_location: str, entries: list[dict], course_info: dict, results: dict) -> dict:
    def course_entry(e: dict) -> dict:
        rating, rating_by_category = parse_rating(e.get("rating"), e["course"])
        return {
            "course": e["course"], "title": course_info[e["course"]][0],
            "units": course_info[e["course"]][1], "prerequisites": course_info[e["course"]][2],
            "category": e.get("category") or [],
            "rating": rating,
            "rating_by_category": rating_by_category,
            "offered_in": [{"semester": sem, "minis": results[(e["course"], sem)]["minis"],
                "meetings": results[(e["course"], sem)]["meetings"],
                "link": results[(e["course"], sem)]["link"]}
                for sem in semesters if results.get((e["course"], sem)) is not None],
        }

    return {
        "generated": today.isoformat(timespec="seconds"),
        "semesters_checked": semesters,
        "teaching_location": teaching_location,
        "courses": [course_entry(e) for e in entries],
    }


def export_report(today, years: int) -> bool:
    print("Fetching available semesters from SOC...")
    semesters = filter_semesters(available_semesters(), today, years)
    if not semesters:
        print("ERROR: could not retrieve semester list from SOC.")
        return False
    print(f"Checking semesters: {', '.join(semesters)}")
    with open(PLAN_CONFIG, encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    teaching_location = validate_teaching_location(cfg.get("teaching_location"))
    entries = sorted(cfg["courses"], key=lambda e: e["course"])
    results = probe_offerings(entries, semesters, teaching_location)
    course_info = resolve_course_info(entries, semesters, results)
    valid_entries = [entry for entry in entries if entry["course"] in course_info]
    html = build_report_html(build_report_rows(valid_entries, course_info, results, semesters), today, years, teaching_location)
    OUT_DIR.mkdir(exist_ok=True)
    REPORT_OUTPUT.write_text(html, encoding="utf-8")
    print(f"Report written  -> {REPORT_OUTPUT}")
    snapshot = build_snapshot(today, semesters, teaching_location, valid_entries, course_info, results)
    SNAPSHOT.write_text(json.dumps(snapshot, indent=2), encoding="utf-8")
    print(f"Snapshot written -> {SNAPSHOT}")
    return True
