import json
import re
import unittest

from cmu_course_planner.degree_planner.models import Course, Offering, SectionOption
from cmu_course_planner.degree_planner.render import build_html


def course(course_id: str) -> Course:
    return Course(
        course=course_id,
        title=f"Course {course_id}",
        units=12,
        prerequisites="None",
        category=[],
        rating=3,
        rating_by_category={},
        offered_in=[Offering("F26", [], [SectionOption("A", [])], "https://example.test")],
        selected_section="A",
    )


class LazyDegreePlannerRenderTests(unittest.TestCase):
    def test_report_embeds_raw_inputs_for_the_worker_and_no_generated_paths(self) -> None:
        first = course("first")
        first.offered_in[0].section_options.append(SectionOption("B", []))
        second = course("second")
        rendered = build_html([first, second], ["F"], [12], [], "Pittsburgh, Pennsylvania", "test snapshot", [])
        self.assertIn('class="route-tree" role="tree"', rendered)
        self.assertEqual(rendered.count('class="route-panel"'), 2)
        self.assertIn('id="degree-worker-source"', rendered)
        match = re.search(r'<script type="application/json" id="degree-path-data">(.*?)</script>', rendered)
        self.assertIsNotNone(match)
        data = json.loads(match.group(1))
        self.assertEqual(len(data["terms"]), 1)
        term = data["terms"][0]
        self.assertNotIn("choices", term)
        self.assertNotIn("fragments", term)
        self.assertEqual([option["label"] for option in term["options"][0]], ["A", "B"])
        self.assertIn("Semester 1 - Fall", term["heading"])
        self.assertIn("Course first", term["options"][0][0]["row"])
        self.assertIn("Course second", term["options"][1][0]["row"])
        self.assertEqual(data["courses"][0]["units"], 12)


if __name__ == "__main__":
    unittest.main()
