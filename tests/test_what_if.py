import unittest
from dataclasses import replace

from cmu_course_planner.common.prerequisites import PrerequisiteStatus
from cmu_course_planner.suggest.models import Course, Meeting, Offering, SectionOption
from cmu_course_planner.suggest.what_if import analyze_swap, build_what_if_data


def course(
    course_id: str,
    units: int = 12,
    begin: str = "9:00AM",
    end: str = "9:50AM",
    mini: int | None = None,
    prerequisite_status: PrerequisiteStatus = "none",
) -> Course:
    option = SectionOption(
        label="A",
        meetings=[Meeting("M", begin, end, mini)],
        mini=mini,
    )
    return Course(
        course=course_id,
        title=f"Course {course_id}",
        units=units,
        prerequisites="15-213" if prerequisite_status != "none" else "None",
        category=[],
        rating=3,
        rating_by_category={},
        offered_in=[Offering("F26", [mini] if mini else [], [option], "https://example.test")],
        prerequisite_status=prerequisite_status,
    )


class WhatIfAnalysisTests(unittest.TestCase):
    def test_reports_exact_time_conflict(self) -> None:
        result = analyze_swap(
            course("candidate"),
            "F",
            [],
            12,
            [Meeting("M", "9:30AM", "10:20AM", label="17-622 Agile Methods")],
            None,
        )

        self.assertEqual(result["status"], "rejected")
        self.assertIn("17-622 Agile Methods (M 9:30AM–10:20AM)", result["reasons"][0])

    def test_removing_a_course_can_make_the_swap_work(self) -> None:
        scheduled = replace(course("scheduled"), selected_section="A")
        candidate = course("candidate", begin="10:00AM", end="10:50AM")

        keep = analyze_swap(candidate, "F", [scheduled], 12, [], None)
        swap = analyze_swap(candidate, "F", [scheduled], 12, [], scheduled)

        self.assertEqual(keep["status"], "rejected")
        self.assertIn("24/12 units", keep["reasons"][0])
        self.assertEqual(swap["status"], "works")
        self.assertEqual(swap["unitsAfter"], 12)

    def test_reports_mini_workload_limit(self) -> None:
        scheduled = replace(course("scheduled", units=6, mini=1), selected_mini=1, selected_section="A")
        candidate = course("candidate", units=6, mini=1, begin="10:00AM", end="10:50AM")

        result = analyze_swap(candidate, "F", [scheduled], 12, [], None)

        self.assertEqual(result["status"], "rejected")
        self.assertIn("Mini workload limit exceeded", result["reasons"][0])
        self.assertEqual(analyze_swap(candidate, "F", [scheduled], 24, [], None)["status"], "works")

    def test_unsatisfied_prerequisite_is_a_warning_not_a_schedule_block(self) -> None:
        result = analyze_swap(
            course("candidate", prerequisite_status="unsatisfied"),
            "F",
            [],
            12,
            [],
            None,
        )

        self.assertEqual(result["status"], "works")
        self.assertIn("Prerequisite is marked unsatisfied", result["warnings"][0])

    def test_data_includes_every_semester_and_removal_choice(self) -> None:
        scheduled = replace(course("scheduled"), selected_section="A")
        data = build_what_if_data(
            ["F", "S"],
            [[scheduled], []],
            [course("candidate")],
            [12, 12],
            [],
        )

        semesters = data["courses"][0]["semesters"]
        self.assertEqual([semester["label"] for semester in semesters], [
            "Semester 1 · Fall",
            "Semester 2 · Spring",
        ])
        self.assertEqual([semester["offered"] for semester in semesters], [True, False])
        self.assertEqual([swap["remove"] for swap in semesters[0]["swaps"]], ["", "scheduled"])
        self.assertEqual(semesters[1]["swaps"][0]["summary"], "No detected offering")

    def test_fixed_course_is_not_offered_as_a_removal(self) -> None:
        fixed = replace(
            course("fixed"),
            selected_section="A",
            fixed_semester=1,
        )
        planned = replace(course("planned"), selected_section="A")

        data = build_what_if_data(
            ["F"],
            [[fixed, planned]],
            [course("candidate")],
            [24],
            [],
        )

        swaps = data["courses"][0]["semesters"][0]["swaps"]
        self.assertEqual([swap["remove"] for swap in swaps], ["", "planned"])

    def test_each_semester_uses_its_own_unit_cap(self) -> None:
        scheduled = replace(course("scheduled"), selected_section="A")

        data = build_what_if_data(
            ["F", "F"],
            [[scheduled], [scheduled]],
            [course("candidate", begin="10:00AM", end="10:50AM")],
            [18, 24],
            [],
        )

        semesters = data["courses"][0]["semesters"]
        self.assertEqual(semesters[0]["swaps"][0]["status"], "rejected")
        self.assertIn("24/18 units", semesters[0]["swaps"][0]["reasons"][0])
        self.assertEqual(semesters[1]["swaps"][0]["status"], "works")
        self.assertIn("24/24 units", semesters[1]["swaps"][0]["summary"])


if __name__ == "__main__":
    unittest.main()
