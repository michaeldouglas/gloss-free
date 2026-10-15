from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from typer.testing import CliRunner

from libras_translation import cli


class FakeAcquisition:
    def __init__(self):
        self.calls = []

    def run(self, dataset, destination, **kwargs):
        self.calls.append((dataset, destination, kwargs))
        if kwargs.get("list_only"):
            return {
                "commit": "a" * 40,
                "listed": 1,
                "total_bytes": 1024,
                "unknown_sizes": 0,
                "manifest": {
                    "files": {
                        "videos/test.mp4": {
                            "remote_path": "videos/test.mp4",
                            "expected_size_bytes": 1024,
                        }
                    }
                },
            }
        if kwargs.get("progress"):
            kwargs["progress"](1, 1)
        return {
            "downloaded": 1,
            "skipped": 2,
            "auxiliary_downloaded": 1,
            "failed": 0,
            "commit": "a" * 40,
            "manifest_path": "data/manifests/test.json",
        }


class CliTests(unittest.TestCase):
    def setUp(self):
        self.runner = CliRunner()

    def invoke(self, args):
        """Execute the CLI with deterministic, non-colored output."""
        return self.runner.invoke(cli.app, args, color=False)

    def test_help_exposes_data_subcommands_and_examples_of_options(self):
        root_help = self.invoke(["--help"])
        data_help = self.invoke(["data", "--help"])
        list_help = self.invoke(["data", "list", "--help"])
        download_help = self.invoke(["data", "download", "--help"])
        self.assertEqual(root_help.exit_code, 0, root_help.output)
        self.assertIn("data", root_help.output)
        self.assertIn("list", data_help.output)
        self.assertIn("download", data_help.output)
        self.assertIn("--show-files", list_help.output)
        self.assertIn("--workers", download_help.output)

    def test_download_requires_explicit_dataset_without_prompting(self):
        result = self.invoke(["data", "download"])
        self.assertEqual(result.exit_code, 2)
        self.assertIn("--dataset", result.output)

    def test_invoking_without_arguments_shows_help_without_prompting(self):
        result = self.invoke([])
        self.assertEqual(result.exit_code, 2)
        self.assertIn("Usage:", result.output)
        self.assertNotIn("Selecione", result.output)

    def test_invalid_dataset_uses_usage_exit_code(self):
        result = self.invoke(["data", "download", "--dataset", "unknown"])
        self.assertEqual(result.exit_code, 2)

    def test_list_calls_application_service_and_renders_rich_summary(self):
        service = FakeAcquisition()
        with patch.object(cli, "_acquisition", return_value=service):
            result = self.invoke(
                ["data", "list", "--dataset", "minds-libras-raw", "--limit", "1"],
            )
        self.assertEqual(result.exit_code, 0, result.output)
        self.assertIn("1.0 KiB", result.output)
        self.assertEqual(service.calls[0][0], "minds-libras-raw")
        self.assertTrue(service.calls[0][2]["list_only"])

    def test_download_passes_options_and_renders_summary(self):
        service = FakeAcquisition()
        target = Path("E:/research-data")
        with patch.object(cli, "_acquisition", return_value=service):
            result = self.invoke(
                ["data", "download", "--dataset", "minds-libras-raw",
                 "--destination", str(target), "--limit", "2", "--workers", "3"],
            )
        self.assertEqual(result.exit_code, 0, result.output)
        self.assertIn("Resumo da aquisição", result.output)
        self.assertEqual(service.calls[0][1], target.resolve())
        self.assertEqual(service.calls[0][2]["limit"], 2)
        self.assertEqual(service.calls[0][2]["workers"], 3)

    def test_validate_metadata_renders_summary_and_uses_explicit_output(self):
        payload = {
            "summary": {
                "videos_seen": 3,
                "videos_ok": 2,
                "videos_with_probe_error": 1,
                "fps_rate_matches": 1,
                "fps_frame_count_matches": 1,
                "fps_inconclusive": 1,
            }
        }
        with TemporaryDirectory() as temporary_directory:
            output = Path(temporary_directory) / "metadata-validation"
            with patch.object(cli, "validate_dataset", return_value=payload) as validator:
                result = self.invoke(
                    [
                        "video",
                        "validate-metadata",
                        "--dataset",
                        "v-librasil-raw",
                        "--output",
                        str(output),
                        "--fps-tolerance",
                        "0.02",
                    ]
                )

        self.assertEqual(result.exit_code, 0, result.output)
        self.assertIn("Vídeos vistos", result.output)
        self.assertIn("Resultados:", result.output)
        self.assertEqual(validator.call_args.kwargs["dataset"], "v-librasil-raw")
        self.assertEqual(validator.call_args.args[2], output.resolve())
        self.assertEqual(validator.call_args.kwargs["fps_tolerance"], 0.02)

    def test_validate_metadata_returns_nonzero_for_input_or_tool_failure(self):
        with patch.object(cli, "validate_dataset", side_effect=OSError("ffprobe ausente")):
            result = self.invoke(
                [
                    "video",
                    "validate-metadata",
                    "--dataset",
                    "v-librasil-raw",
                ]
            )

        self.assertEqual(result.exit_code, 1, result.output)
        self.assertIn("ffprobe ausente", result.output)

    def test_validate_quality_emits_decision_and_returns_nonzero_for_no_go(self):
        payload = {
            "summary": {
                "decision": "NO-GO",
                "counts": {"CRITICAL": 1, "ERROR": 0, "WARNING": 0, "INFO": 0},
                "artifacts": {"manifest": "manifest.parquet"},
            }
        }
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            with patch.object(cli, "validate_dataset"), patch.object(
                cli, "generate_validation_artifacts_from_file", return_value={"summary": payload["summary"]}
            ) as generator:
                result = self.invoke(
                    [
                        "video",
                        "validate-quality",
                        "--dataset",
                        "v-librasil-raw",
                        "--metadata-output",
                        str(root / "technical"),
                        "--output-root",
                        str(root / "quality"),
                    ]
                )

        self.assertEqual(result.exit_code, 2, result.output)
        self.assertIn("NO-GO", result.output)
        self.assertEqual(generator.call_args.kwargs["dataset"], "v-librasil-raw")


if __name__ == "__main__":
    unittest.main()
