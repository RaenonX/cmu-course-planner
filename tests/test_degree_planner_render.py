import base64
import gzip
import json
import re
import unittest
from dataclasses import replace

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
    def test_all_routes_are_listed_but_bodies_are_compressed(self) -> None:
        first = course("first")
        first_section_b = replace(first, selected_section="B")
        second = course("second")
        routes = [
            ([[first]], [second]),
            ([[first_section_b]], [second]),
            ([[second]], [first]),
        ]

        rendered = build_html(
            ["F"],
            [("Rating First", "Test routes", routes)],
            [12],
            [],
            "Pittsburgh, Pennsylvania",
            "test snapshot",
            [first, second],
            [],
        )

        self.assertEqual(rendered.count('class="route-tree-leaf'), 3)
        self.assertEqual(rendered.count('class="route-panel"'), 1)
        self.assertIn('class="route-tree" role="tree"', rendered)
        self.assertEqual(rendered.count("Semester 1 · first"), 1)
        self.assertIn('<span class="route-tree-count">2 routes</span>', rendered)
        self.assertIn("Semester 1 · second", rendered)
        self.assertNotIn("route-tab-bar", rendered)
        match = re.search(
            r'<script type="application/json" class="route-data">(.*?)</script>',
            rendered,
        )
        self.assertIsNotNone(match)
        payloads = json.loads(match.group(1))
        self.assertEqual(len(payloads), 3)
        bodies = [gzip.decompress(base64.b64decode(value)).decode() for value in payloads]
        self.assertIn("Semester 1 - Fall", bodies[0])
        self.assertIn("Course first", bodies[0])
        self.assertIn("Course first", bodies[1])
        self.assertIn("Course second", bodies[2])


if __name__ == "__main__":
    unittest.main()
