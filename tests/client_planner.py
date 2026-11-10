"""Exercise the actual browser solver from Python's existing course fixtures."""

import json
import subprocess
from dataclasses import replace
from pathlib import Path

from cmu_course_planner.common.config import USER_TO_SOC
from cmu_course_planner.degree_planner.route_payload import build_path_data


def run_client(courses, semesters, caps, current, prefer=None, **request):
    data = build_path_data(courses, semesters, caps, prefer or [], current)
    process = subprocess.run(
        ["node", str(Path(__file__).with_name("client_planner_runner.cjs"))],
        input=json.dumps({"data": data, **request}), text=True, encoding="utf-8",
        capture_output=True, check=True,
    )
    result = json.loads(process.stdout)
    if "error" in result:
        raise ValueError(result["error"])
    return result


def selected_courses(courses, semester, choices):
    selected = []
    for course_id, option_id in choices:
        course = courses[course_id]
        option = course.offering_for(USER_TO_SOC[semester]).section_options[option_id]
        selected.append(replace(course, selected_mini=option.mini, selected_section=option.label))
    return selected


def client_paths(courses, semesters, caps, current):
    result = run_client(courses, semesters, caps, current)
    return {
        "count": int(result["count"]),
        "choices": [[selected_courses(courses, semester, choice) for choice in choices]
                    for semester, choices in zip(semesters, result["choices"])],
    }


def plan_degree(courses, semesters, caps, prefer, current, variant="Rating First"):
    result = run_client(courses, semesters, caps, current, prefer, operation="first",
                        variant=int(variant == "Time Continuity First"))
    schedule = [selected_courses(courses, semester, choices)
                for semester, choices in zip(semesters, result["choices"])]
    assigned = {c.course for selected in schedule for c in selected}
    return schedule, [c for c in courses if c.course not in assigned]


def selection_ids(courses, semester, selected):
    ids = {c.course: i for i, c in enumerate(courses)}
    return [[ids[c.course], next(i for i, option in enumerate(c.offering_for(USER_TO_SOC[semester]).section_options)
                                if option.label == c.selected_section and option.mini == c.selected_mini)]
            for c in selected]


def analyze_swap(course, soc, selected, cap, current, removed):
    semester = "Su" if soc == "M" else soc
    courses = [*selected, course]
    return run_client(courses, [semester], [cap], current, operation="whatIf", index=0,
                      selected=selection_ids(courses, semester, selected), course=len(selected),
                      remove=next((i for i, c in enumerate(selected) if c is removed), None))


def build_what_if_data(semesters, schedule, unplaced, caps, current):
    courses = list({c.course: c for selected in [*schedule, unplaced] for c in selected}.values())
    return run_client(courses, semesters, caps, current, operation="routeWhatIf",
                      schedule=[selection_ids(courses, sem, selected) for sem, selected in zip(semesters, schedule)])
