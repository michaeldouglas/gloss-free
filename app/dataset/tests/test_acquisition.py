import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from libras_translation import config
from libras_translation.config import PROJECT_ROOT, Settings
from libras_translation.acquisition import DatasetAcquisition
from libras_translation.cli import prompt_options
from libras_translation.infrastructure.huggingface_client import RemoteFile


class FakeClient:
    def __init__(self):
        self.paths = []

    def resolve_commit(self, repo_id):
        return "a" * 40

    def list_videos(self, repo_id, commit):
        self.paths.append((repo_id, commit))
        return [RemoteFile("videos/subpasta/vídeo.mp4", 4), RemoteFile("videos/outro.mp4", None)]

    def list_repo_files(self, repo_id, commit):
        self.paths.append((repo_id, commit))
        return [
            RemoteFile("videos/subpasta/vídeo.mp4", 4),
            RemoteFile("videos/outro.mp4", None),
            RemoteFile("annotations.csv", 4),
            RemoteFile("error.csv", 4),
        ]

    def download(self, repo_id, commit, path, destination):
        target = Path(destination, *Path(path).parts)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(b"data")
        return str(target)


class AcquisitionTests(unittest.TestCase):
    def test_interactive_prompt_collects_all_acquisition_options(self):
        answers = iter(["minds-libras-raw", "2", "2", "E:/datasets", "3", "s"])
        options = prompt_options(lambda _prompt: next(answers))
        self.assertEqual(options["selected"], ["minds-libras-raw"])
        self.assertTrue(options["list_only"])
        self.assertEqual(options["limit"], 2)
        self.assertEqual(options["destination"], Path("E:/datasets"))
        self.assertEqual(options["workers"], 3)
        self.assertTrue(options["verbose"])

    def test_interactive_prompt_applies_defaults_and_accepts_both_datasets(self):
        answers = iter(["3", "", "", "", "", ""])
        options = prompt_options(lambda _prompt: next(answers))
        self.assertEqual(options["selected"], list(config.DATASETS))
        self.assertFalse(options["list_only"])
        self.assertIsNone(options["limit"])
        self.assertIsNone(options["destination"])
        self.assertEqual(options["workers"], 4)
        self.assertFalse(options["verbose"])

    def test_token_is_read_from_environment_without_logging_it(self):
        with patch.dict(os.environ, {"HF_TOKEN": "hf_test_placeholder"}):
            self.assertEqual(Settings.hf_token(), "hf_test_placeholder")
        self.assertEqual(PROJECT_ROOT, Path(__file__).resolve().parents[2])

    def test_token_is_loaded_from_project_dotenv_independent_of_current_directory(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / ".env").write_text("HF_TOKEN=hf_dotenv_placeholder\n", encoding="utf-8")
            with patch.dict(os.environ):
                os.environ.pop("HF_TOKEN", None)
                with patch.object(config, "PROJECT_ROOT", root):
                    self.assertEqual(Settings.hf_token(), "hf_dotenv_placeholder")

    def test_list_only_pins_commit_and_writes_manifest(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            client = FakeClient()
            result = DatasetAcquisition(client, root / "manifests").run(
                "v-librasil-raw", root / "raw", list_only=True
            )
            self.assertEqual(result["listed"], 2)
            self.assertEqual(result["unknown_sizes"], 1)
            self.assertEqual(client.paths[0][1], result["commit"])
            manifest = json.loads((root / "manifests/v-librasil-raw.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["files"]["videos/subpasta/vídeo.mp4"]["status"], "pending")
            self.assertEqual(manifest["auxiliary_files"]["annotations.csv"]["status"], "pending")

    def test_download_preserves_unicode_path_and_repeat_skips_complete_file(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            client = FakeClient()
            use_case = DatasetAcquisition(client, root / "manifests")
            first = use_case.run("v-librasil-raw", root / "raw", workers=2)
            second = use_case.run("v-librasil-raw", root / "raw", workers=2)
            self.assertEqual(first["failed"], 0)
            self.assertTrue((root / "raw/v-librasil-raw/videos/subpasta/vídeo.mp4").is_file())
            self.assertTrue((root / "raw/v-librasil-raw/annotations.csv").is_file())
            self.assertTrue((root / "raw/v-librasil-raw/error.csv").is_file())
            self.assertEqual(second["skipped"], 2)

    def test_limit_restricts_videos_but_keeps_dataset_metadata(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            client = FakeClient()
            result = DatasetAcquisition(client, root / "manifests").run(
                "v-librasil-raw", root / "raw", limit=1
            )
            self.assertEqual(result["listed"], 1)
            self.assertTrue((root / "raw/v-librasil-raw/annotations.csv").is_file())
            self.assertTrue((root / "raw/v-librasil-raw/videos/subpasta/vídeo.mp4").is_file())
            self.assertFalse((root / "raw/v-librasil-raw/videos/outro.mp4").exists())


if __name__ == "__main__":
    unittest.main()
