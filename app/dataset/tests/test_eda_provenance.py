from __future__ import annotations

import unittest
import shutil
from pathlib import Path
from tempfile import TemporaryDirectory

import pandas as pd

from libras_translation.analysis.dataset_profile import build_execution_provenance
from libras_translation.analysis.output_contract import create_private_run, publish_run_atomically
from libras_translation.analysis.stage2 import load_published_stage2, run_stage2_eda
from libras_translation.analysis.synthesis import build_evidence_map, render_synthesis_report


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
            root = Path(temporary) / "eda"
            result = run_stage2_eda(output_root=root, executed_at="20261107T040000Z")
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
