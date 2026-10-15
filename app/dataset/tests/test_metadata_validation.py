from __future__ import annotations

import csv
import json
import tempfile
import unittest
from decimal import Decimal
from pathlib import Path

from libras_translation.metadata_validation import (
    classify_fps_hypotheses,
    validate_dataset,
)


def fake_probe(path: Path) -> dict:
    if path.name == "broken.mp4":
        return {"status": "error", "error": {"message": "fixture inválido"}}
    return {
        "status": "ok",
        "actual_width": 160,
        "actual_height": 120,
        "actual_fps": 25.0,
        "actual_fps_source": "avg_frame_rate",
        "actual_frame_count": 50,
        "actual_frame_count_source": "nb_frames",
        "actual_duration_seconds": 2.0,
        "actual_duration_source": "format.duration",
        "codec": "mpeg4",
        "field_status": {
            "width": "available",
            "height": "available",
            "fps": "available",
            "frame_count": "available",
        },
        "error": None,
    }


class MetadataValidationTests(unittest.TestCase):
    def test_fps_hypotheses_are_independent_and_use_tolerance(self):
        rate = classify_fps_hypotheses(
            Decimal("25.005"), "available", 25.0, "available", 50, "available"
        )
        self.assertEqual(rate["fps_rate_status"], "match")
        self.assertEqual(rate["fps_frame_count_status"], "mismatch")
        self.assertEqual(rate["fps_hypothesis"], "rate")

        frame_count = classify_fps_hypotheses(
            Decimal("50"), "available", 25.0, "available", 50, "available"
        )
        self.assertEqual(frame_count["fps_hypothesis"], "frame_count")

        ambiguous = classify_fps_hypotheses(
            Decimal("25"), "available", 25.0, "available", 25, "available"
        )
        self.assertEqual(ambiguous["fps_hypothesis"], "ambiguous")

    def test_validation_writes_json_source_and_preserves_inputs(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            videos = root / "videos"
            output = root / "processed"
            videos.mkdir()
            (videos / "rate.mp4").write_bytes(b"rate fixture")
            (videos / "frame_count.mp4").write_bytes(b"frame fixture")
            (videos / "broken.mp4").write_bytes(b"broken fixture")
            annotations = root / "annotations.csv"
            annotations.write_text(
                "video_name,width,height,fps\n"
                "rate.mp4,160,120,25.005\n"
                "frame_count.mp4,160,120,50\n"
                "broken.mp4,160,120,25\n",
                encoding="utf-8",
            )
            before = {path.name: path.read_bytes() for path in videos.iterdir()}

            result = validate_dataset(
                annotations,
                videos,
                output,
                dataset="fixture",
                probe_function=fake_probe,
                tool_runner=lambda *args, **kwargs: type(
                    "Completed", (), {"returncode": 0, "stdout": "ffprobe version fixture", "stderr": ""}
                )(),
            )

            self.assertEqual(result["schema_version"], "video-metadata-validation.v1")
            self.assertEqual(result["summary"]["videos_seen"], 3)
            self.assertEqual(result["summary"]["fps_rate_matches"], 1)
            self.assertEqual(result["summary"]["fps_frame_count_matches"], 1)
            self.assertTrue((output / "metadata_validation.json").is_file())
            self.assertTrue((output / "metadata_comparison.csv").is_file())
            self.assertTrue((output / "video_metadata.csv").is_file())
            self.assertTrue((output / "fps_hypotheses_summary.csv").is_file())
            self.assertTrue((output / "validation.log").is_file())
            self.assertEqual(before, {path.name: path.read_bytes() for path in videos.iterdir()})

            stored = json.loads((output / "metadata_validation.json").read_text(encoding="utf-8"))
            rate_result = next(item for item in stored["results"] if item["input"]["relative_path"] == "rate.mp4")
            broken_result = next(item for item in stored["results"] if item["input"]["relative_path"] == "broken.mp4")
            self.assertEqual(rate_result["comparison"]["csv_fps_raw"], "25.005")
            self.assertEqual(broken_result["probe"]["status"], "error")

    def test_missing_csv_video_is_error_but_other_files_continue(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            videos = root / "videos"
            videos.mkdir()
            (videos / "present.mp4").write_bytes(b"fixture")
            (videos / "extra.mp4").write_bytes(b"fixture")
            annotations = root / "annotations.csv"
            annotations.write_text(
                "video_name,width,height,fps\n"
                "present.mp4,160,120,25\n"
                "missing.mp4,160,120,25\n",
                encoding="utf-8",
            )
            result = validate_dataset(
                annotations,
                videos,
                root / "processed",
                probe_function=fake_probe,
                tool_runner=lambda *args, **kwargs: type(
                    "Completed", (), {"returncode": 0, "stdout": "ffprobe version fixture", "stderr": ""}
                )(),
            )
            self.assertEqual(len(result["results"]), 3)
            missing = next(item for item in result["results"] if item["input"]["relative_path"] == "missing.mp4")
            present = next(item for item in result["results"] if item["input"]["relative_path"] == "present.mp4")
            extra = next(item for item in result["results"] if item["input"]["relative_path"] == "extra.mp4")
            self.assertEqual(missing["probe"]["status"], "error")
            self.assertEqual(missing["comparison"]["overall_status"], "error")
            self.assertEqual(present["comparison"]["overall_status"], "match")
            self.assertEqual(extra["comparison"]["fps_hypothesis"], "not_in_csv")
            self.assertEqual(result["summary"]["dataset_fps_interpretation"], "rate")

    def test_probe_exception_is_recorded_per_file_and_does_not_stop_batch(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            videos = root / "videos"
            videos.mkdir()
            (videos / "present.mp4").write_bytes(b"fixture")
            (videos / "raises.mp4").write_bytes(b"fixture")
            annotations = root / "annotations.csv"
            annotations.write_text(
                "video_name,width,height,fps\n"
                "present.mp4,160,120,25\n"
                "raises.mp4,160,120,25\n",
                encoding="utf-8",
            )

            def raising_probe(path: Path) -> dict:
                if path.name == "raises.mp4":
                    raise RuntimeError("erro controlado")
                return fake_probe(path)

            result = validate_dataset(
                annotations,
                videos,
                root / "processed",
                probe_function=raising_probe,
                tool_runner=lambda *args, **kwargs: type(
                    "Completed", (), {"returncode": 0, "stdout": "ffprobe version fixture", "stderr": ""}
                )(),
            )
            self.assertEqual(len(result["results"]), 2)
            raises = next(item for item in result["results"] if item["input"]["relative_path"] == "raises.mp4")
            present = next(item for item in result["results"] if item["input"]["relative_path"] == "present.mp4")
            self.assertEqual(raises["probe"]["status"], "error")
            self.assertIn("erro controlado", raises["probe"]["error"]["message"])
            self.assertEqual(present["comparison"]["overall_status"], "match")

    def test_optional_error_csv_is_included_without_overriding_annotations(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            videos = root / "videos"
            videos.mkdir()
            (videos / "annotated.mp4").write_bytes(b"fixture")
            (videos / "exception.mp4").write_bytes(b"fixture")
            annotations = root / "annotations.csv"
            annotations.write_text(
                "video_name,width,height,fps\nannotated.mp4,160,120,25\n",
                encoding="utf-8",
            )
            exceptions = root / "error.csv"
            exceptions.write_text(
                "video_name,width,height,fps\n"
                "annotated.mp4,1,2,3\n"
                "exception.mp4,160,120,50\n",
                encoding="utf-8",
            )

            result = validate_dataset(
                annotations,
                videos,
                root / "processed",
                exceptions_csv=exceptions,
                probe_function=fake_probe,
                tool_runner=lambda *args, **kwargs: type(
                    "Completed", (), {"returncode": 0, "stdout": "ffprobe version fixture", "stderr": ""}
                )(),
            )

            annotated = next(item for item in result["results"] if item["input"]["relative_path"] == "annotated.mp4")
            exception = next(item for item in result["results"] if item["input"]["relative_path"] == "exception.mp4")
            self.assertEqual(annotated["csv"]["_csv_source"], "annotations.csv")
            self.assertEqual(exception["csv"]["_csv_source"], "error.csv")
            self.assertEqual(exception["comparison"]["fps_hypothesis"], "frame_count")


if __name__ == "__main__":
    unittest.main()
