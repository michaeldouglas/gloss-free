from __future__ import annotations

import csv
import shutil
import tempfile
import unittest
from pathlib import Path

from libras_translation.stage1_review import build_stage1_review, normalize_stage1_key


class Stage1ReviewTests(unittest.TestCase):
    def _fixture(self):
        root = Path(tempfile.mkdtemp()) / "v-librasil-raw"
        self.addCleanup(shutil.rmtree, root.parent)
        (root / "videos").mkdir(parents=True)
        rows = [
            {"video_id": "id-a", "video_name": 'Cérebro (de "ervilha")_Articulador1.mp4', "class": 'Cérebro (de "ervilha")', "user_id": "Articulador1", "width": "1920", "height": "1080", "fps": "30", "url_page": "https://example.test/a", "url_download": "https://example.test/a.mp4"},
            {"video_id": "id-b", "video_name": r"Frente\Á Frente_Articulador1.mp4", "class": r"Frente\Á Frente", "user_id": "Articulador1", "width": "1920", "height": "1080", "fps": "900", "url_page": "https://example.test/b", "url_download": "https://example.test/b.mp4"},
        ]
        with (root / "annotations.csv").open("w", encoding="utf-8", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)
        (root / "error.csv").write_text("video_name,width,height,fps\nCongelar_Articulador3.mp4,0,0,0\n", encoding="utf-8")
        for row in rows:
            physical_name = row["video_name"].replace('"', "\uf022").replace("\\", "\uf05c")
            (root / "videos" / physical_name).write_bytes(b"fixture")
        manifest = [{**row, "source_csv": "annotations.csv", "file_exists": True, "file_readable": True, "actual_width": 1920, "actual_height": 1080, "actual_fps": 30, "actual_frame_count": 900, "actual_duration": 30, "codec": "h264", "filename_valid": True, "metadata_match": "match", "technical_valid": True, "dataset_valid": True} for row in rows]
        technical = {"run": {"fps_tolerance": 0.01}, "results": [{"csv": {"video_name": rows[0]["video_name"]}, "input": {"relative_path": rows[0]["video_name"]}, "probe": {"status": "ok", "actual_fps_source": "avg_frame_rate", "actual_frame_count_source": "nb_frames"}, "comparison": {"width_status": "match", "height_status": "match", "fps_rate_status": "match", "fps_frame_count_status": "mismatch", "overall_status": "match"}}, {"csv": {"video_name": rows[1]["video_name"]}, "input": {"relative_path": rows[1]["video_name"]}, "probe": {"status": "ok", "actual_fps_source": "avg_frame_rate", "actual_frame_count_source": "nb_frames"}, "comparison": {"width_status": "match", "height_status": "match", "fps_rate_status": "mismatch", "fps_frame_count_status": "match", "overall_status": "match"}}]}
        summary = {"key_reconciliation": {"csv_records": 2}, "counts": {"issues": 0, "affected_files": 0, "affected_annotations": 0, "by_severity": {"CRITICAL": 0, "ERROR": 0, "WARNING": 0, "INFO": 0}}, "source_integrity": {"annotations_before": "a", "annotations_after": "a", "error_before": "e", "error_after": "e", "video_inventory_before": "v", "video_inventory_after": "v"}}
        return root, rows, manifest, technical, summary

    def test_normalization_keeps_backslash_literal(self):
        self.assertEqual(normalize_stage1_key(r" Frente\Á Frente_Articulador1.mp4 "), normalize_stage1_key("Frente\uf05cÁ Frente_Articulador1.mp4"))
        self.assertNotIn("/á frente", normalize_stage1_key(r"Frente\Á Frente_Articulador1.mp4"))

    def test_review_reads_raw_counts_and_sources(self):
        root, _, manifest, technical, summary = self._fixture()
        review = build_stage1_review(root, technical, summary, manifest)
        self.assertEqual(review["reconciliation"]["annotations_recalculated"], 2)
        self.assertEqual(review["reconciliation"]["physical_files_recalculated"], 2)
        self.assertEqual(review["reconciliation"]["matched"], 2)
        self.assertEqual(review["fps_analysis"]["confidence"], "low/undetermined")
        self.assertEqual(review["fps_analysis"]["hypothesis_winner"], "undetermined")
        self.assertEqual(review["fps_analysis"]["rate_source_counts"], {"avg_frame_rate": 2})
        self.assertEqual(review["requirements"][0]["status"], "PASS")
        self.assertEqual(review["source_artifacts"]["technical"], "data/processed/metadata-validation/v-librasil-raw/metadata_validation.json")
        self.assertEqual(len(review["requirements"]), 7)

    def test_physical_extra_and_collision_are_detected_independently_of_manifest(self):
        root, _, manifest, technical, summary = self._fixture()
        (root / "videos" / "A").mkdir()
        (root / "videos" / "B").mkdir()
        (root / "videos" / "A" / "extra.mp4").write_bytes(b"extra")
        (root / "videos" / "B" / "EXTRA.mp4").write_bytes(b"extra")
        review = build_stage1_review(root, technical, summary, manifest)
        self.assertEqual(review["reconciliation"]["extras"], 1)
        self.assertIn("extra.mp4", review["reconciliation"]["collisions"]["physical"])
        self.assertEqual(review["requirements"][2]["status"], "FAIL")


if __name__ == "__main__":
    unittest.main()
