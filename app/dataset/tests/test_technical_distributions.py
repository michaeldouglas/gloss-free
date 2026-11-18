from __future__ import annotations

import unittest

import pandas as pd

from libras_translation.analysis.distributions import analyze_technical_distributions


class TechnicalDistributionTests(unittest.TestCase):
    def test_technical_tables_keep_denominator_and_missing_measurement(self):
        frame = pd.DataFrame(
            {
                "actual_width": [640, None, 1280],
                "actual_height": [480, 720, 720],
                "actual_fps": [30.0, 30.0, None],
                "codec": ["h264", None, "h265"],
            }
        )
        result = analyze_technical_distributions(
            {"v-librasil-raw": frame, "minds-libras-raw": frame.copy(deep=True)}
        )
        numeric = result["technical_distribution_statistics"]
        categorical = result["technical_frequency_tables"]
        self.assertEqual(set(numeric["denominator"]), {3})
        self.assertIn("aspect_ratio", set(numeric["variable"]))
        self.assertTrue((numeric["n"] + numeric["missing_failure_of_measurement"] == 3).all())
        self.assertEqual(int(categorical.loc[categorical["variable"] == "codec", "count"].sum()), 6)


if __name__ == "__main__":
    unittest.main()
