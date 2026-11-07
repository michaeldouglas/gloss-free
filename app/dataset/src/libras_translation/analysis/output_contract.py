"""Canonical output layout and publication rules for Stage 2."""

from __future__ import annotations

import json
import os
import shutil
import uuid
from pathlib import Path
from typing import Any


EDA_OUTPUT_CONTRACT = {
    "root": "data/processed/eda",
    "current_directories": ["reports", "tables", "figures", "snapshots", "provenance"],
    "archive_directory": "archive/<run_id>",
    "run_id": "UTC timestamp plus short code commit, e.g. 20261104T001321Z-abcdef0",
    "canonical_marker": "provenance/CURRENT.json",
    "publication": "write to a private run directory, validate, then publish atomically and update CURRENT.json",
    "overwrite": "never overwrite an archived run; current publication may advance only through an explicit canonical publication step",
    "figures": "empty until EDA is explicitly executed",
}


def output_directories(root: Path) -> dict[str, Path]:
    return {name: root / name for name in EDA_OUTPUT_CONTRACT["current_directories"]}


def create_private_run(output_root: Path, run_id: str) -> Path:
    """Create an isolated run directory before any publication is attempted."""

    run_root = output_root / "archive" / run_id
    run_root.mkdir(parents=True, exist_ok=False)
    for directory in EDA_OUTPUT_CONTRACT["current_directories"]:
        (run_root / directory).mkdir(parents=True, exist_ok=True)
    return run_root


def read_current(output_root: Path) -> dict[str, Any] | None:
    marker = output_root / "provenance" / "CURRENT.json"
    if not marker.is_file():
        return None
    return json.loads(marker.read_text(encoding="utf-8"))


def output_hashes(root: Path) -> dict[str, str]:
    """Return stable SHA-256 hashes for files below a run or publication root."""

    import hashlib

    hashes: dict[str, str] = {}
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        hashes[path.relative_to(root).as_posix()] = digest
    return hashes


def _write_json_atomic(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def publish_run_atomically(
    run_root: Path,
    output_root: Path,
    current: dict[str, Any],
) -> list[str]:
    """Promote a validated run as the current publication with rollback."""

    required = set(EDA_OUTPUT_CONTRACT["current_directories"])
    missing = sorted(name for name in required if not (run_root / name).is_dir())
    if missing:
        raise ValueError(f"execução incompleta; diretórios ausentes: {missing}")

    output_root.mkdir(parents=True, exist_ok=True)
    staging = output_root / f".publish-{run_root.name}"
    backup = output_root / f".previous-{run_root.name}"
    shutil.rmtree(staging, ignore_errors=True)
    shutil.rmtree(backup, ignore_errors=True)
    staging.mkdir(parents=True, exist_ok=False)
    backup.mkdir(parents=True, exist_ok=False)
    for directory in EDA_OUTPUT_CONTRACT["current_directories"]:
        shutil.copytree(run_root / directory, staging / directory)
    _write_json_atomic(staging / "provenance" / "CURRENT.json", current)

    moved: list[str] = []
    try:
        for directory in EDA_OUTPUT_CONTRACT["current_directories"]:
            target = output_root / directory
            previous = backup / directory
            if target.exists():
                os.replace(target, previous)
            os.replace(staging / directory, target)
            moved.append(directory)
    except Exception:
        for directory in reversed(moved):
            target = output_root / directory
            if target.exists():
                shutil.rmtree(target)
            previous = backup / directory
            if previous.exists():
                os.replace(previous, target)
        raise
    finally:
        shutil.rmtree(staging, ignore_errors=True)
        shutil.rmtree(backup, ignore_errors=True)

    return [
        path.relative_to(output_root).as_posix()
        for path in sorted(output_root.rglob("*"))
        if path.is_file() and not any(part.startswith(".") for part in path.relative_to(output_root).parts)
    ]
