from __future__ import annotations

import unittest

import pandas as pd

from libras_translation.analysis.comparison import compare_class_sets, compare_datasets, compare_numeric_datasets


def _frames() -> dict[str, pd.DataFrame]:
    base = {
        "class": ["A", "A", "B"],
        "user_id": ["u1", "u2", "u1"],
        "actual_frame_count": [10, 20, 30],
        "actual_duration": [1.0, 2.0, 3.0],
        "actual_fps": [10.0, 10.0, 10.0],
        "actual_width": [640, 640, 1280],
        "actual_height": [480, 480, 720],
    }
    other = {**base, "class": ["A", "C", "C"]}
    return {"v-librasil-raw": pd.DataFrame(base), "minds-libras-raw": pd.DataFrame(other)}


class ComparisonTests(unittest.TestCase):
    def test_numeric_comparison_retains_dataset_and_denominator(self):
        result = compare_numeric_datasets(_frames())
        self.assertEqual(len(result), 12)
        self.assertEqual(set(result["dataset"]), {"v-librasil-raw", "minds-libras-raw"})
        self.assertEqual(set(result["denominator"]), {3})
        self.assertEqual(set(result["unit"]), {"frames", "s", "frames/s", "pixels", "razão largura/altura"})

    def test_shared_and_exclusive_classes_are_descriptive_only(self):
        result = compare_class_sets(_frames())
        self.assertEqual(set(result.loc[result["class"] == "A", "membership"]), {"shared"})
        self.assertEqual(set(result.loc[result["class"] == "B", "membership"]), {"v-librasil-raw_only"})
        self.assertEqual(set(result.loc[result["class"] == "C", "membership"]), {"minds-libras-raw_only"})
        self.assertEqual(set(result["denominator"]), {3})

    def test_comparison_bundle_keeps_tables_separate(self):
        bundle = compare_datasets(_frames())
        self.assertEqual(set(bundle), {"numeric", "classes"})


if __name__ == "__main__":
    unittest.main()
