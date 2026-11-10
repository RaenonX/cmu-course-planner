import unittest
from itertools import product

from cmu_course_planner.degree_planner.priority import _route_choice_index
from cmu_course_planner.degree_planner.variants import ROUTE_ATTEMPTS


class RouteSearchTests(unittest.TestCase):
    def test_independent_decisions_explore_all_binary_combinations(self) -> None:
        combinations = {
            tuple(_route_choice_index(seed, 0, position, 2) for position in range(3))
            for seed in range(ROUTE_ATTEMPTS)
        }
        self.assertEqual(combinations, set(product(range(2), repeat=3)))

    def test_choices_are_not_limited_to_first_twelve_candidates(self) -> None:
        choices = {
            _route_choice_index(seed, 0, 0, 20)
            for seed in range(ROUTE_ATTEMPTS)
        }
        self.assertEqual(choices, set(range(20)))

if __name__ == "__main__":
    unittest.main()
