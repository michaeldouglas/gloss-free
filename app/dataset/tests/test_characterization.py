from __future__ import annotations

import unittest

import pandas as pd

from libras_translation.analysis.characterization import characterize_dataset


class CharacterizationTests(unittest.TestCase):
    def test_part1_tables_preserve_denominator_and_crossed_factor_counts(self):
        frame = pd.DataFrame(
            {
                "class": ["A", "A", "B"],
                "user_id": ["u1", "u2", "u1"],
                "actual_frame_count": [10, 20, 30],
                "actual_duration": [1.0, 2.0, 3.0],
                "actual_fps": [10.0, 10.0, 10.0],
                "actual_width": [640, 640, 1280],
                "actual_height": [480, 480, 720],
                "codec": ["h264", "h264", "h264"],
            }
        )
        tables = characterize_dataset(frame, "minds-libras-raw")

        overview = tables["overview"].iloc[0]
        self.assertEqual(int(overview["videos"]), 3)
        self.assertEqual(int(overview["classes_unique"]), 2)
        self.assertEqual(int(overview["signers_unique"]), 2)
        self.assertEqual(int(overview["class_user_combinations_unique"]), 3)
        self.assertEqual(int(tables["class_counts"]["count"].sum()), 3)
        self.assertEqual(int(tables["signer_counts"]["count"].sum()), 3)
        self.assertEqual(int(tables["class_signer_counts"]["count"].sum()), 3)
        self.assertEqual(set(tables["numeric"]["missing_applicable"]), {0})
        self.assertEqual(set(tables["categorical"]["denominator"]), {3})


if __name__ == "__main__":
    unittest.main()
