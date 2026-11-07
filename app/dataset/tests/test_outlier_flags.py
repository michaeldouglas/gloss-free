from __future__ import annotations

import unittest

import pandas as pd

from libras_translation.analysis.outliers import flag_dataset_outliers, flag_outliers


class OutlierFlagTests(unittest.TestCase):
    def _frame(self) -> pd.DataFrame:
        return pd.DataFrame(
            {
                "filesystem_key": ["a", "b", "c", "d", "e"],
                "class": ["A"] * 5,
                "user_id": ["u1"] * 5,
                "actual_frame_count": [10, 11, 12, 13, 100],
                "actual_duration": [1, 1, 1, 1, 10],
                "actual_fps": [30, 30, 30, 30, 30],
                "actual_width": [640] * 5,
                "actual_height": [480] * 5,
            }
        )

    def test_iqr_flags_preserve_scale_and_input_rows(self):
        frame = self._frame()
        original = frame.copy(deep=True)
        result = flag_outliers(frame, "minds-libras-raw", "actual_frame_count")
        self.assertEqual(set(result["filesystem_key"]), {"e"})
        self.assertTrue((result["recommended_action"].str.contains("sem remover")).all())
        pd.testing.assert_frame_equal(frame, original)

    def test_mad_and_percentile_methods_are_supported(self):
        frame = self._frame()
        self.assertFalse(flag_outliers(frame, "minds-libras-raw", "actual_duration", method="mad", threshold=2).empty)
        self.assertFalse(flag_outliers(frame, "minds-libras-raw", "actual_duration", method="percentile", threshold=0.1).empty)

    def test_dataset_bundle_is_non_destructive(self):
        frame = self._frame()
        before = len(frame)
        result = flag_dataset_outliers(frame, "minds-libras-raw")
        self.assertEqual(len(frame), before)
        self.assertTrue(set(result["variable"]).issuperset({"actual_frame_count", "actual_duration"}))


if __name__ == "__main__":
    unittest.main()
