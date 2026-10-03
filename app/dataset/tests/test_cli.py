from __future__ import annotations

import unittest
from pathlib import Path
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

    def test_help_exposes_data_subcommands_and_examples_of_options(self):
        root_help = self.runner.invoke(cli.app, ["--help"])
        data_help = self.runner.invoke(cli.app, ["data", "--help"])
        list_help = self.runner.invoke(cli.app, ["data", "list", "--help"])
        download_help = self.runner.invoke(cli.app, ["data", "download", "--help"])
        self.assertEqual(root_help.exit_code, 0, root_help.output)
        self.assertIn("data", root_help.output)
        self.assertIn("list", data_help.output)
        self.assertIn("download", data_help.output)
        self.assertIn("--show-files", list_help.output)
        self.assertIn("--workers", download_help.output)

    def test_download_requires_explicit_dataset_without_prompting(self):
        result = self.runner.invoke(cli.app, ["data", "download"])
        self.assertEqual(result.exit_code, 2)
        self.assertIn("--dataset", result.output)

    def test_invoking_without_arguments_shows_help_without_prompting(self):
        result = self.runner.invoke(cli.app, [])
        self.assertEqual(result.exit_code, 2)
        self.assertIn("Usage:", result.output)
        self.assertNotIn("Selecione", result.output)

    def test_invalid_dataset_uses_usage_exit_code(self):
        result = self.runner.invoke(cli.app, ["data", "download", "--dataset", "unknown"])
        self.assertEqual(result.exit_code, 2)

    def test_list_calls_application_service_and_renders_rich_summary(self):
        service = FakeAcquisition()
        with patch.object(cli, "_acquisition", return_value=service):
            result = self.runner.invoke(
                cli.app,
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
            result = self.runner.invoke(
                cli.app,
                ["data", "download", "--dataset", "minds-libras-raw",
                 "--destination", str(target), "--limit", "2", "--workers", "3"],
            )
        self.assertEqual(result.exit_code, 0, result.output)
        self.assertIn("Resumo da aquisição", result.output)
        self.assertEqual(service.calls[0][1], target.resolve())
        self.assertEqual(service.calls[0][2]["limit"], 2)
        self.assertEqual(service.calls[0][2]["workers"], 3)


if __name__ == "__main__":
    unittest.main()
