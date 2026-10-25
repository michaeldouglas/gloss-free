from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from libras_translation.dataset_quality_validation import generate_validation_artifacts
from libras_translation.metadata_validation import validate_dataset


def fake_probe(path: Path) -> dict:
    if path.name == "broken.mp4":
        return {"status": "error", "error": {"message": "fixture ilegível"}}
    return {
        "status": "ok",
        "actual_width": 160,
        "actual_height": 120,
        "actual_fps": 25.0,
        "actual_frame_count": 50,
        "actual_duration_seconds": 2.0,
        "codec": "mpeg4",
        "field_status": {
            "width": "available",
            "height": "available",
            "fps": "available",
            "frame_count": "available",
        },
        "error": None,
    }


class DatasetQualityValidationTests(unittest.TestCase):
    def _technical_result(self, root: Path, dataset: str, *, annotations: str, errors: str = "") -> dict:
        dataset_root = root / dataset
        videos = dataset_root / "videos"
        videos.mkdir(parents=True)
        (videos / "valid_Articulador1.mp4").write_bytes(b"valid")
        (videos / "extra.mp4").write_bytes(b"extra")
        (videos / "broken.mp4").write_bytes(b"broken")
        (dataset_root / "annotations.csv").write_text(annotations, encoding="utf-8")
        if errors:
            (dataset_root / "error.csv").write_text(errors, encoding="utf-8")
        output = root / "technical" / dataset
        return validate_dataset(
            dataset_root / "annotations.csv",
            videos,
            output,
            dataset=dataset,
            exceptions_csv=dataset_root / "error.csv" if errors else None,
            probe_function=fake_probe,
            tool_runner=lambda *args, **kwargs: type(
                "Completed", (), {"returncode": 0, "stdout": "ffprobe fixture", "stderr": ""}
            )(),
        )

    def test_reconciles_error_csv_and_writes_report_summary_and_parquet(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            dataset_root = root / "v-librasil-raw"
            payload = self._technical_result(
                root,
                "v-librasil-raw",
                annotations=(
                    "video_name,class,user_id,width,height,fps\n"
                    "valid_Articulador1.mp4,valid,Articulador1,160,120,25\n"
                    "missing_Articulador1.mp4,missing,Articulador1,160,120,25\n"
                ),
                errors=(
                    "video_name,class,user_id,width,height,fps\n"
                    "known_Articulador1.mp4,known,Articulador1,0,0,0\n"
                ),
            )
            output_root = root / "quality"
            before = (dataset_root / "videos" / "valid_Articulador1.mp4").read_bytes()

            result = generate_validation_artifacts(
                dataset="v-librasil-raw",
                dataset_root=dataset_root,
                metadata_payload=payload,
                output_root=output_root,
            )

            codes = {issue["code"] for issue in result["issues"]}
            self.assertIn("silent_missing_file", codes)
            self.assertIn("known_missing_file", codes)
            self.assertIn("unregistered_physical_file", codes)
            self.assertEqual(result["summary"]["decision"], "NO-GO")
            self.assertTrue((output_root / "reports" / "metadata_validation_report.md").is_file())
            self.assertTrue((output_root / "reports" / "metadata_issues.csv").is_file())
            self.assertTrue((output_root / "reports" / "metadata_summary.json").is_file())
            manifest = output_root / "manifests" / "v_librasil_validated.parquet"
            self.assertTrue(manifest.is_file())
            stored = json.loads((output_root / "reports" / "metadata_summary.json").read_text(encoding="utf-8"))
            self.assertEqual(stored["decision"], "NO-GO")
            self.assertEqual(stored["counts"]["manifest_rows"], 5)
            self.assertEqual(before, (dataset_root / "videos" / "valid_Articulador1.mp4").read_bytes())

            import pandas as pd

            frame = pd.read_parquet(manifest)
            self.assertIn("actual_width", frame.columns)
            self.assertIn("file_exists", frame.columns)
            self.assertIn("filename_valid", frame.columns)
            self.assertIn("metadata_valid", frame.columns)

    def test_unknown_dataset_can_go_with_no_error_csv_and_keeps_filename_uncertainty(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            payload = self._technical_result(
                root,
                "minds-libras-raw",
                annotations="video_id,video_name,width,height,fps\nvalid_Articulador1.mp4,valid_Articulador1.mp4,160,120,25\n",
            )
            (root / "minds-libras-raw" / "videos" / "extra.mp4").unlink()
            (root / "minds-libras-raw" / "videos" / "broken.mp4").unlink()
            result = generate_validation_artifacts(
                dataset="minds-libras-raw",
                dataset_root=root / "minds-libras-raw",
                metadata_payload=payload,
                output_root=root / "quality",
            )

            self.assertEqual(result["summary"]["decision"], "GO")
            self.assertTrue(any(issue["code"] == "error_csv_absent" for issue in result["issues"]))
            self.assertTrue((root / "quality" / "manifests" / "minds_libras_validated.parquet").is_file())

    def test_minds_joins_by_video_id_and_reports_descriptive_name_relation(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            dataset_root = root / "minds-libras-raw"
            videos = dataset_root / "videos"
            videos.mkdir(parents=True)
            physical_name = "01AcontecerSinalizador01-1.mp4"
            (videos / physical_name).write_bytes(b"valid")
            (dataset_root / "annotations.csv").write_text(
                "video_id,video_name,class,user_id,width,height,fps\n"
                f"{physical_name},Acontecer_Sinalizador01-1.mp4,Acontecer,Sinalizador01,160,120,50\n",
                encoding="utf-8",
            )
            payload = validate_dataset(
                dataset_root / "annotations.csv",
                videos,
                root / "technical",
                dataset="minds-libras-raw",
                probe_function=fake_probe,
                tool_runner=lambda *args, **kwargs: type(
                    "Completed", (), {"returncode": 0, "stdout": "ffprobe fixture", "stderr": ""}
                )(),
            )

            result = generate_validation_artifacts(
                dataset="minds-libras-raw",
                dataset_root=dataset_root,
                metadata_payload=payload,
                output_root=root / "quality",
            )

            self.assertEqual(result["summary"]["decision"], "GO")
            reconciliation = result["summary"]["key_reconciliation"]
            self.assertEqual(reconciliation["filesystem_key_column"], "video_id")
            self.assertEqual(reconciliation["csv_records"], 1)
            self.assertEqual(reconciliation["physical_files"], 1)
            self.assertEqual(reconciliation["matched"], 1)
            self.assertEqual(reconciliation["missing"], 0)
            self.assertEqual(reconciliation["extra"], 0)
            self.assertEqual(result["summary"]["video_name_analysis"]["relation_counts"], {"deterministic_prefix_and_separator": 1})
            codes = {issue["code"] for issue in result["issues"]}
            self.assertNotIn("silent_missing_file", codes)
            self.assertNotIn("unregistered_physical_file", codes)
            self.assertNotIn("filename_invalid", codes)
            import pandas as pd

            manifest = pd.read_parquet(root / "quality" / "manifests" / "minds_libras_validated.parquet")
            self.assertEqual(len(manifest), 1)
            self.assertEqual(manifest.iloc[0]["video_id"], physical_name)
            self.assertEqual(manifest.iloc[0]["video_name"], "Acontecer_Sinalizador01-1.mp4")
            self.assertEqual(manifest.iloc[0]["filesystem_key_column"], "video_id")

    def test_error_reason_is_flagged_when_zero_marker_has_a_readable_file(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            payload = self._technical_result(
                root,
                "v-librasil-raw",
                annotations="video_name,class,user_id,width,height,fps\nvalid_Articulador1.mp4,valid,Articulador1,160,120,25\n",
                errors="video_name,class,user_id,width,height,fps\nvalid_Articulador1.mp4,valid,Articulador1,0,0,0\n",
            )
            result = generate_validation_artifacts(
                dataset="v-librasil-raw",
                dataset_root=root / "v-librasil-raw",
                metadata_payload=payload,
                output_root=root / "quality",
            )

            self.assertTrue(any(issue["code"] == "exception_reason_inconsistent" for issue in result["issues"]))
            self.assertTrue(any(issue["code"] == "error_csv_missing" for issue in result["issues"]) is False)


if __name__ == "__main__":
    unittest.main()
