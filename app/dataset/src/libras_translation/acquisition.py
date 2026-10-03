from __future__ import annotations

import json
import logging
import os
import tempfile
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Callable

from huggingface_hub.errors import HfHubHTTPError, RepositoryNotFoundError
from .config import DATASETS
from .infrastructure.huggingface_client import HuggingFaceClient, RemoteFile

LOGGER = logging.getLogger(__name__)
MAX_ATTEMPTS = 4


def format_size(size: int | None) -> str:
    if size is None:
        return "desconhecido"
    value = float(size)
    for unit in ("B", "KiB", "MiB", "GiB", "TiB"):
        if value < 1024 or unit == "TiB":
            return f"{value:.1f} {unit}"
        value /= 1024
    return f"{size} B"


def _atomic_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            "w", encoding="utf-8", dir=path.parent, delete=False, suffix=".tmp"
        ) as stream:
            temp_path = Path(stream.name)
            json.dump(payload, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
        os.replace(temp_path, path)
    finally:
        if temp_path and temp_path.exists():
            temp_path.unlink()


def _error_message(error: Exception) -> str:
    if isinstance(error, RepositoryNotFoundError):
        return "Repositório inexistente ou privado; verifique o identificador, HF_TOKEN e a permissão de leitura."
    if isinstance(error, HfHubHTTPError) and getattr(error.response, "status_code", None) in (401, 403):
        return "Acesso negado pelo Hugging Face; verifique HF_TOKEN e a autorização para o dataset."
    if isinstance(error, (ConnectionError, TimeoutError, OSError)) or getattr(error, "response", None) is not None:
        return f"Falha de rede/armazenamento após tentativas: {type(error).__name__}: {error}"
    return f"{type(error).__name__}: {error}"


class DatasetAcquisition:
    def __init__(self, client: HuggingFaceClient, manifests_dir: Path) -> None:
        self.client = client
        self.manifests_dir = manifests_dir

    def run(
        self,
        dataset: str,
        destination: Path,
        *,
        list_only: bool = False,
        limit: int | None = None,
        workers: int = 4,
        progress: Callable[[int, int], None] | None = None,
    ) -> dict:
        if dataset not in DATASETS:
            raise ValueError(f"Dataset desconhecido: {dataset}")
        if workers < 1:
            raise ValueError("A concorrência deve ser pelo menos 1.")
        if limit is not None and limit < 1:
            raise ValueError("O limite deve ser pelo menos 1.")

        repo_id = DATASETS[dataset]
        commit = self.client.resolve_commit(repo_id)
        repo_files = self.client.list_repo_files(repo_id, commit)
        files = [file for file in repo_files if file.path.startswith("videos/")]
        if limit is not None:
            files = files[:limit]
        auxiliary_files = [file for file in repo_files if not file.path.startswith("videos/")]

        target_root = destination / dataset
        manifest_path = self.manifests_dir / f"{dataset}.json"
        manifest = self._new_or_resume_manifest(manifest_path, repo_id, commit, files)
        manifest["auxiliary_files"] = self._new_or_resume_entries(
            manifest.get("auxiliary_files", {}), auxiliary_files
        )
        if list_only:
            _atomic_json(manifest_path, manifest)
            return {"dataset": dataset, "repo_id": repo_id, "commit": commit,
                    "listed": len(files), "total_bytes": sum(f.size or 0 for f in files),
                    "unknown_sizes": sum(f.size is None for f in files), "manifest": manifest}

        target_root.mkdir(parents=True, exist_ok=True)
        lock = threading.Lock()
        total = len(files) + len(auxiliary_files)
        done = 0
        failures = 0
        with ThreadPoolExecutor(max_workers=workers) as executor:
            future_files = {
                executor.submit(self._download_one, repo_id, commit, file, target_root): file
                for file in [*files, *auxiliary_files]
            }
            for future in as_completed(future_files):
                file = future_files[future]
                try:
                    state, error = future.result(), None
                except Exception as exc:  # record individual failures and continue
                    state, error = "failed", _error_message(exc)
                    failures += 1
                    LOGGER.error("Falha em %s: %s", file.path, error)
                with lock:
                    group = "files" if file.path.startswith("videos/") else "auxiliary_files"
                    entry = manifest[group][file.path]
                    entry["status"] = state
                    entry["error"] = error
                    entry["local_path"] = str((target_root / PurePosixPath(file.path)).resolve())
                    _atomic_json(manifest_path, manifest)
                done += 1
                if progress:
                    progress(done, total)

        return {"dataset": dataset, "repo_id": repo_id, "commit": commit,
                "listed": len(files), "downloaded": sum(v["status"] == "downloaded" for v in manifest["files"].values()),
                "skipped": sum(v["status"] == "skipped_existing" for v in manifest["files"].values()),
                "auxiliary_downloaded": sum(v["status"] == "downloaded" for v in manifest["auxiliary_files"].values()),
                "failed": failures, "manifest_path": str(manifest_path)}

    def _download_one(self, repo_id: str, commit: str, file: RemoteFile, target_root: Path) -> str:
        relpath = PurePosixPath(file.path)
        if relpath.is_absolute() or ".." in relpath.parts:
            raise ValueError(f"Caminho remoto inseguro: {file.path}")
        target = target_root.joinpath(*relpath.parts)
        if target.is_file() and (file.size is None or target.stat().st_size == file.size):
            return "skipped_existing"
        target.parent.mkdir(parents=True, exist_ok=True)
        last_error: Exception | None = None
        for attempt in range(MAX_ATTEMPTS):
            try:
                self.client.download(repo_id, commit, file.path, str(target_root))
                if not target.is_file():
                    raise OSError(f"Download concluído sem arquivo no destino esperado: {target}")
                if file.size is not None and target.stat().st_size != file.size:
                    raise OSError(f"Tamanho inesperado para {file.path}: {target.stat().st_size} de {file.size} bytes")
                return "downloaded"
            except Exception as exc:
                last_error = exc
                if attempt + 1 < MAX_ATTEMPTS:
                    delay = 2 ** attempt
                    LOGGER.warning("Tentativa %d/%d falhou para %s; nova tentativa em %ds.", attempt + 1, MAX_ATTEMPTS, file.path, delay)
                    time.sleep(delay)
        assert last_error is not None
        raise last_error

    @staticmethod
    def _new_or_resume_entries(prior: dict, files: list[RemoteFile]) -> dict:
        entries = {}
        for file in files:
            previous_file = prior.get(file.path, {})
            entries[file.path] = {
                "remote_path": file.path,
                "local_path": previous_file.get("local_path"),
                "expected_size_bytes": file.size,
                "status": previous_file.get("status", "pending"),
                "error": previous_file.get("error"),
            }
        return entries

    @staticmethod
    def _new_or_resume_manifest(path: Path, repo_id: str, commit: str, files: list[RemoteFile]) -> dict:
        prior = {}
        if path.exists():
            try:
                previous = json.loads(path.read_text(encoding="utf-8"))
                if previous.get("repo_id") == repo_id and previous.get("commit") == commit:
                    prior = previous.get("files", {})
            except (OSError, json.JSONDecodeError):
                LOGGER.warning("Manifesto anterior inválido; será reconstruído: %s", path)
        entries = DatasetAcquisition._new_or_resume_entries(prior, files)
        return {"repo_id": repo_id, "commit": commit,
                "acquired_at_utc": datetime.now(timezone.utc).isoformat(), "files": entries}
