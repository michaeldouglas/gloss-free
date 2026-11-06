from __future__ import annotations

import hashlib
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import pandas as pd

from libras_translation.analysis.data_dictionary import DATA_DICTIONARY, classify_missingness, manifest_field_definitions
from libras_translation.analysis.dataset_profile import (
    DATASET_CONTRACTS,
    build_input_identity,
    deterministic_group_counts,
    load_validated_manifest,
    validate_manifest_contract,
)


APP_ROOT = Path(__file__).resolve().parents[2]


class AnalysisContractTests(unittest.TestCase):
    def test_canonical_manifests_have_expected_population_and_unique_physical_key(self):
        for dataset, contract in DATASET_CONTRACTS.items():
            try:
                frame = load_validated_manifest(dataset)
            except FileNotFoundError:
                self.skipTest(f"manifest canônico não disponível localmente: {dataset}")
            self.assertEqual(len(frame), contract.expected_rows)
            self.assertEqual(frame[contract.physical_key_column].nunique(), len(frame))
            self.assertEqual(frame[contract.manifest_key_column].nunique(), len(frame))
            self.assertTrue(frame[contract.validity_column].all())
            self.assertEqual(set(frame.columns), {field.name for field in manifest_field_definitions(dataset)})

    def test_minds_structural_null_is_not_missing_data(self):
        self.assertEqual(classify_missingness("minds-libras-raw", "filename_valid", None), "structural_absence")
        self.assertEqual(classify_missingness("minds-libras-raw", "actual_duration", None), "failure_of_measurement")

    def test_same_named_identifiers_keep_dataset_specific_semantics(self):
        v = {field.name: field for field in DATA_DICTIONARY["v-librasil-raw"]}
        m = {field.name: field for field in DATA_DICTIONARY["minds-libras-raw"]}
        self.assertIn("não é a chave física", v["video_id"].description)
        self.assertIn("Nome do arquivo físico", v["video_name"].description)
        self.assertIn("identifica fisicamente", m["video_id"].description)
        self.assertIn("não identifica fisicamente", m["video_name"].description)

    def test_grouping_is_deterministic_and_preserves_null_group(self):
        frame = pd.DataFrame({"user_id": ["B", "A", "B", None], "class": ["x", "x", "y", "z"]})
        first = deterministic_group_counts(frame, "user_id")
        second = deterministic_group_counts(frame, "user_id")
        pd.testing.assert_frame_equal(first, second)
        self.assertEqual(first["count"].sum(), len(frame))

    def test_contract_rejects_duplicate_physical_key_without_mutating_frame(self):
        frame = pd.DataFrame({
            "filesystem_key": ["a", "a"],
            "dataset_valid": [True, True],
        })
        original = frame.copy(deep=True)
        with self.assertRaises(ValueError):
            validate_manifest_contract(frame, "v-librasil-raw")
        pd.testing.assert_frame_equal(frame, original)

    def test_v_librasil_exception_policy_is_external_to_validated_rows(self):
        contract = DATASET_CONTRACTS["v-librasil-raw"]
        self.assertEqual(contract.expected_rows, 4086)
        self.assertEqual(contract.exception_count, 3)
        self.assertIn("fora do corpus analítico", contract.exception_policy)

    def test_input_identity_is_reproducible_for_same_manifest(self):
        for dataset in DATASET_CONTRACTS:
            try:
                first = build_input_identity(dataset)
                second = build_input_identity(dataset)
            except FileNotFoundError:
                self.skipTest(f"manifest canônico não disponível localmente: {dataset}")
            self.assertEqual(first, second)

    def test_canonical_input_bytes_are_not_changed_by_read(self):
        for dataset in DATASET_CONTRACTS:
            try:
                path = DATASET_CONTRACTS[dataset]
                frame = load_validated_manifest(dataset)
            except FileNotFoundError:
                self.skipTest(f"manifest canônico não disponível localmente: {dataset}")
            manifest_path = Path(
                APP_ROOT,
                "data",
                "processed",
                "metadata-validation",
                dataset,
                "manifests",
                path.manifest_filename,
            )
            before = hashlib.sha256(manifest_path.read_bytes()).hexdigest()
            self.assertEqual(len(frame), path.expected_rows)
            after = hashlib.sha256(manifest_path.read_bytes()).hexdigest()
            self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()
