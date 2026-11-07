from __future__ import annotations

import unittest

import pandas as pd

from libras_translation.analysis.distributions import (
    TEMPORAL_FIELDS,
    analyze_temporal_distributions,
    temporal_distribution_statistics,
    temporal_extreme_candidates,
    temporal_percentiles,
)
from libras_translation.analysis.distributions import (
    analyze_technical_distributions,
    derive_aspect_ratio,
    technical_distribution_statistics,
    technical_frequency_table,
)


def _frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "filesystem_key": ["a.mp4", "b.mp4", "c.mp4", "d.mp4", "e.mp4"],
            "class": ["A", "A", "B", "B", "C"],
            "user_id": ["u1", "u1", "u2", "u2", "u3"],
            "actual_frame_count": [10, 11, 12, 13, 100],
            "actual_duration": [1.0, 1.1, 1.2, 1.3, 10.0],
            "actual_fps": [30.0, 30.0, 30.1, 30.1, 30.2],
        }
    )


class DistributionTests(unittest.TestCase):
    def test_statistics_keep_original_scale_and_denominator(self):
        frame = _frame()
        original = frame.copy(deep=True)
        stats = temporal_distribution_statistics(frame, "minds-libras-raw")

        self.assertEqual(set(stats["variable"]), set(TEMPORAL_FIELDS))
        self.assertEqual(set(stats["denominator"]), {5})
        self.assertEqual(set(stats["n"]), {5})
        self.assertEqual(set(stats["missing_real"]), {0})
        self.assertTrue((stats["coefficient_of_variation"] > 0).all())
        pd.testing.assert_frame_equal(frame, original)

    def test_missing_values_are_counted_without_imputation(self):
        frame = _frame()
        frame.loc[4, "actual_duration"] = None
        stats = temporal_distribution_statistics(frame, "minds-libras-raw")
        row = stats.loc[stats["variable"].eq("actual_duration")].iloc[0]

        self.assertEqual(int(row["denominator"]), 5)
        self.assertEqual(int(row["n"]), 4)
        self.assertEqual(int(row["missing_real"]), 1)

    def test_percentiles_and_iqr_candidates_are_reproducible(self):
        frame = _frame()
        first = temporal_percentiles(frame, "minds-libras-raw")
        second = temporal_percentiles(frame.copy(deep=True), "minds-libras-raw")
        pd.testing.assert_frame_equal(first, second)

        candidates = temporal_extreme_candidates(frame, "minds-libras-raw")
        self.assertIn("actual_frame_count", set(candidates["variable"]))
        self.assertIn("actual_duration", set(candidates["variable"]))
        self.assertTrue(set(candidates["flag"]).issubset({"below_iqr_lower_fence", "above_iqr_upper_fence"}))
        self.assertEqual(set(candidates["filesystem_key"]), {"e.mp4"})

    def test_combined_analysis_keeps_datasets_separate(self):
        analysis = analyze_temporal_distributions(
            {
                "v-librasil-raw": _frame(),
                "minds-libras-raw": _frame(),
            }
        )
        for table in analysis.values():
            self.assertEqual(set(table["dataset"]), {"v-librasil-raw", "minds-libras-raw"})

    def test_technical_summaries_are_derived_without_mutating_manifest(self):
        frame = _frame().assign(actual_width=[640, 640, 1280, 1280, 0], actual_height=[480, 480, 720, 720, 0], codec=["h264", "h264", "h265", None, "h265"])
        original = frame.copy(deep=True)
        ratios = derive_aspect_ratio(frame)
        self.assertAlmostEqual(float(ratios.iloc[0]), 4 / 3)
        self.assertTrue(pd.isna(ratios.iloc[4]))
        stats = technical_distribution_statistics(frame, "minds-libras-raw")
        self.assertEqual(set(stats["denominator"]), {5})
        self.assertIn("aspect_ratio", set(stats["variable"]))
        frequencies = technical_frequency_table(frame, "minds-libras-raw", "codec")
        self.assertEqual(int(frequencies["count"].sum()), 5)
        self.assertIn("(failure_of_measurement)", set(frequencies["category"]))
        pd.testing.assert_frame_equal(frame, original)

    def test_combined_technical_analysis_keeps_datasets_separate(self):
        frame = _frame().assign(actual_width=[640, 640, 1280, 1280, 1280], actual_height=[480, 480, 720, 720, 720], codec=["h264"] * 5)
        result = analyze_technical_distributions({"v-librasil-raw": frame, "minds-libras-raw": frame.copy(deep=True)})
        self.assertEqual(set(result["technical_distribution_statistics"]["dataset"]), {"v-librasil-raw", "minds-libras-raw"})
        self.assertEqual(set(result["technical_frequency_tables"]["denominator"]), {5})


if __name__ == "__main__":
    unittest.main()
