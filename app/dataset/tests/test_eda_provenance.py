from __future__ import annotations

import unittest
import shutil
from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

import pandas as pd

from libras_translation.analysis.dataset_profile import build_execution_provenance
from libras_translation.analysis.dataset_profile import DATASET_CONTRACTS, canonical_manifest_path
from libras_translation.analysis.data_dictionary import manifest_field_definitions
from libras_translation.analysis.output_contract import create_private_run, publish_run_atomically
from libras_translation.analysis.stage2 import load_published_stage2, run_stage2_eda
from libras_translation.analysis.synthesis import build_evidence_map, render_synthesis_report
from libras_translation.config import Settings


def _write_stage2_manifest_fixtures(project_root: Path) -> tuple[Settings, dict[str, object]]:
    """Create small validated inputs so the integration test needs no local data."""

    settings = Settings(project_root=project_root)
    contracts: dict[str, object] = {}
    for dataset, contract in DATASET_CONTRACTS.items():
        rows = []
        for index in range(4):
            common = {
                "class": f"class-{index % 2}",
                "user_id": f"user-{index % 2}",
                "width": "640",
                "height": "480",
                "fps": "30",
                "actual_width": 640,
                "actual_height": 480,
                "actual_fps": 30.0,
                "actual_frame_count": 30 + index,
                "actual_duration": 1.0 + index / 10,
                "codec": "h264",
            }
            if dataset == "v-librasil-raw":
                row = {
                    **common,
                    "video_id": f"v-id-{index}",
                    "video_name": f"video-{index}.mp4",
                    "url_page": "https://example.invalid/page",
                    "url_download": "https://example.invalid/video",
                    "dataset": dataset,
                    "source_csv": "annotations.csv",
                    "annotation_row": index + 1,
                    "filesystem_key": f"video-{index}.mp4",
                    "filesystem_original_name": f"video-{index}.mp4",
                    "relative_path": f"videos/video-{index}.mp4",
                    "file_exists": True,
                    "file_readable": True,
                    "filename_valid": True,
                    "metadata_match": "match",
                    "metadata_valid": True,
                    "technical_valid": True,
                    "dataset_valid": True,
                    "validation_status": "valid",
                }
            else:
                row = {
                    **common,
                    "video_id": f"m-id-{index}",
                    "video_name": f"descriptive-name-{index}",
                    "dataset": dataset,
                    "filesystem_key_column": "video_id",
                    "filesystem_key": f"m-id-{index}",
                    "relative_path": f"videos/m-id-{index}.mp4",
                    "source_csv": "annotations.csv",
                    "error_in_annotations": False,
                    "error_file_exists": False,
                    "error_reason_kind": None,
                    "error_reason_consistent": None,
                    "file_exists": True,
                    "file_readable": True,
                    "filename_valid": None,
                    "descriptive_name_status": "deterministic_prefix_and_separator",
                    "descriptive_name_note": "fixture",
                    "metadata_valid": True,
                    "validation_status": "valid",
                    "validation_notes": "fixture",
                }
            rows.append(row)

        path = canonical_manifest_path(dataset, settings=settings)
        path.parent.mkdir(parents=True, exist_ok=True)
        frame = pd.DataFrame(rows, columns=[field.name for field in manifest_field_definitions(dataset)])
        frame.to_parquet(path, index=False)
        contracts[dataset] = replace(contract, expected_rows=len(frame))
    return settings, contracts


class EdaProvenanceTests(unittest.TestCase):
    def test_execution_provenance_keeps_explicit_identity_and_hashes(self):
        identity = {"dataset": "minds-libras-raw", "sha256": "abc", "schema": [{"name": "class", "dtype": "string"}]}
        first = build_execution_provenance(
            input_identities=[identity],
            parameters={"imputation": "none"},
            output_root="data/processed/eda",
            library_versions={"pandas": "2"},
            executed_at="2026-11-07T00:00:00+00:00",
            code_commit="deadbee",
            run_id="run-a",
            published_artifact_hashes={"tables/a.csv": "hash"},
            validation={"all_passed": True},
            decision="COMPLETE WITH NOTES",
        )
        second = build_execution_provenance(
            input_identities=[identity],
            parameters={"imputation": "none"},
            output_root="data/processed/eda",
            library_versions={"pandas": "2"},
            executed_at="2026-11-07T00:00:00+00:00",
            code_commit="deadbee",
            run_id="run-a",
            published_artifact_hashes={"tables/a.csv": "hash"},
            validation={"all_passed": True},
            decision="COMPLETE WITH NOTES",
        )
        self.assertEqual(first, second)
        self.assertEqual(first["inputs"][0]["schema"], identity["schema"])

    def test_synthesis_links_claims_to_artifacts_without_metric_duplication(self):
        current = {"stage": "stage2_eda", "run_id": "run-a", "decision": "COMPLETE WITH NOTES"}
        execution = {"stage": "stage2_eda", "run_id": "run-a", "decision": "COMPLETE WITH NOTES"}
        evidence = build_evidence_map(current=current, execution=execution)
        self.assertIn("evidence", evidence.columns)
        self.assertEqual(set(evidence["run_id"]), {"run-a"})
        with TemporaryDirectory() as temporary:
            report = render_synthesis_report(evidence, Path(temporary) / "reports/synthesis.md", current=current)
            self.assertTrue(report.is_file())
            self.assertIn("mapa de evidências", report.read_text(encoding="utf-8"))

    def test_publication_marker_is_created_only_by_atomic_gate(self):
        with TemporaryDirectory() as temporary:
            root = Path(temporary) / "eda"
            run = create_private_run(root, "run-a")
            (run / "reports" / "a.md").write_text("ok", encoding="utf-8")
            shutil.rmtree(run / "figures")
            with self.assertRaises(ValueError):
                publish_run_atomically(run, root, {"run_id": "run-a"})
            self.assertFalse((root / "provenance/CURRENT.json").exists())

    def test_full_stage2_runner_publishes_all_analysis_parts(self):
        with TemporaryDirectory() as temporary:
            settings, fixture_contracts = _write_stage2_manifest_fixtures(Path(temporary) / "project")
            fixture_settings = settings
            root = Path(temporary) / "eda"
            with patch.dict(DATASET_CONTRACTS, fixture_contracts, clear=True):
                with patch(
                    "libras_translation.analysis.characterization.canonical_manifest_path",
                    side_effect=lambda dataset, settings=None: canonical_manifest_path(
                        dataset, settings=settings or fixture_settings
                    ),
                ), patch(
                    "libras_translation.analysis.distributions.canonical_manifest_path",
                    side_effect=lambda dataset, settings=None: canonical_manifest_path(
                        dataset, settings=settings or fixture_settings
                    ),
                ):
                    result = run_stage2_eda(settings=settings, output_root=root, executed_at="20261107T040000Z")
            published = load_published_stage2(root)
            self.assertTrue(result["validation"]["all_passed"])
            self.assertTrue({
                "tables/dataset_overview.csv",
                "tables/technical_distribution_statistics.csv",
                "tables/comparison_numeric.csv",
                "tables/outlier_flags.csv",
                "tables/evidence_map.csv",
            }.issubset(set(published["current"]["tables"])))
            self.assertEqual(len(published["current"]["figures"]), 29)
            self.assertTrue(result["validation"]["visual_gallery"]["all_passed"])


if __name__ == "__main__":
    unittest.main()
