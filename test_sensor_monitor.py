import unittest

from sensor_monitor import rolling_extrema


class RollingExtremaTests(unittest.TestCase):
    def test_only_complete_windows_are_reported(self):
        self.assertEqual(
            list(rolling_extrema([4, 1, 3, 2], 3)),
            [(4, 1), (3, 1)],
        )

    def test_equal_values_remain_valid_extrema(self):
        self.assertEqual(
            list(rolling_extrema([2, 2, 2, 2], 2)),
            [(2, 2), (2, 2), (2, 2)],
        )

    def test_expired_extrema_are_removed(self):
        self.assertEqual(
            list(rolling_extrema([9, 8, 7, 6, 10], 3)),
            [(9, 7), (8, 6), (10, 6)],
        )

    def test_window_of_one_reports_each_reading(self):
        self.assertEqual(
            list(rolling_extrema([3, -1, 5], 1)),
            [(3, 3), (-1, -1), (5, 5)],
        )

    def test_empty_input_has_no_complete_windows(self):
        self.assertEqual(list(rolling_extrema([], 2)), [])
        self.assertEqual(list(rolling_extrema([1], 2)), [])

    def test_window_size_must_be_a_positive_integer(self):
        for size in (0, -1, 1.5, True):
            with self.subTest(size=size):
                with self.assertRaises(ValueError):
                    rolling_extrema([], size)


if __name__ == "__main__":
    unittest.main()
