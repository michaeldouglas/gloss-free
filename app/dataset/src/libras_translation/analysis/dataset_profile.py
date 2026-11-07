"""Canonical Stage 2 inputs and deterministic manifest-level checks."""

from __future__ import annotations

import hashlib
import subprocess
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from ..config import Settings
from .data_dictionary import manifest_field_definitions


@dataclass(frozen=True)
class DatasetContract:
    dataset: str
    manifest_filename: str
    physical_key_column: str
    manifest_key_column: str
    validity_column: str
    expected_rows: int
    exception_count: int
    exception_policy: str


DATASET_CONTRACTS = {
    "v-librasil-raw": DatasetContract(
        dataset="v-librasil-raw",
        manifest_filename="v_librasil_validated.parquet",
        physical_key_column="filesystem_key",
        manifest_key_column="filesystem_key",
        validity_column="dataset_valid",
        expected_rows=4086,
        exception_count=3,
        exception_policy="error.csv permanece fora do corpus analítico e deve aparecer no denominador documental",
    ),
    "minds-libras-raw": DatasetContract(
        dataset="minds-libras-raw",
        manifest_filename="minds_libras_validated.parquet",
        physical_key_column="video_id",
        manifest_key_column="filesystem_key",
        validity_column="metadata_valid",
        expected_rows=800,
        exception_count=0,
        exception_policy="error.csv ausente é informação de proveniência; não constitui erro",
    ),
}


def canonical_manifest_path(dataset: str, settings: Settings | None = None) -> Path:
    contract = _contract(dataset)
    configured = settings or Settings()
    return configured.processed_data_dir / "metadata-validation" / dataset / "manifests" / contract.manifest_filename


def _contract(dataset: str) -> DatasetContract:
    try:
        return DATASET_CONTRACTS[dataset]
    except KeyError as exc:
        raise ValueError(f"dataset não suportado: {dataset}") from exc


def validate_manifest_contract(
    frame: pd.DataFrame,
    dataset: str,
    *,
    require_expected_rows: bool = False,
) -> None:
    """Validate the Stage 2 input contract without changing the frame."""

    contract = _contract(dataset)
    expected = {field.name for field in manifest_field_definitions(dataset)}
    actual = set(frame.columns)
    missing = sorted(expected - actual)
    extra = sorted(actual - expected)
    if missing or extra:
        details = []
        if missing:
            details.append(f"campos ausentes={missing}")
        if extra:
            details.append(f"campos inesperados={extra}")
        raise ValueError(f"{dataset}: schema incompatível; " + "; ".join(details))
    if require_expected_rows and len(frame) != contract.expected_rows:
        raise ValueError(f"{dataset}: esperado {contract.expected_rows} registros, encontrado {len(frame)}")

    for key_name in (contract.physical_key_column, contract.manifest_key_column):
        if frame[key_name].isna().any():
            raise ValueError(f"{dataset}: chave física nula em {key_name}")
        if frame[key_name].duplicated(keep=False).any():
            raise ValueError(f"{dataset}: chave física duplicada em {key_name}")
    if not frame[contract.validity_column].fillna(False).eq(True).all():
        raise ValueError(f"{dataset}: manifest contém linhas fora do corpus validado")


def load_validated_manifest(dataset: str, *, settings: Settings | None = None) -> pd.DataFrame:
    """Read one canonical manifest; no ffprobe, filtering, or mutation occurs."""

    path = canonical_manifest_path(dataset, settings)
    if not path.is_file():
        raise FileNotFoundError(f"manifest canônico ausente: {path}")
    frame = pd.read_parquet(path)
    validate_manifest_contract(frame, dataset, require_expected_rows=True)
    return frame


def deterministic_group_counts(frame: pd.DataFrame, column: str) -> pd.DataFrame:
    """Return a stable count table for future descriptive grouping."""

    if column not in frame.columns:
        raise KeyError(column)
    result = (
        frame.groupby(column, dropna=False, sort=True, observed=False)
        .size()
        .rename("count")
        .reset_index()
    )
    return result


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_input_identity(dataset: str, *, settings: Settings | None = None) -> dict[str, Any]:
    path = canonical_manifest_path(dataset, settings)
    frame = load_validated_manifest(dataset, settings=settings)
    schema = [
        {"name": column, "dtype": str(frame[column].dtype)}
        for column in frame.columns
    ]
    return {
        "dataset": dataset,
        "path": path.as_posix(),
        "sha256": sha256_file(path),
        "size_bytes": path.stat().st_size,
        "row_count": len(frame),
        "column_count": len(frame.columns),
        "columns": list(frame.columns),
        "schema": schema,
    }


def build_execution_provenance(
    *,
    input_identities: list[dict[str, Any]],
    parameters: dict[str, Any],
    output_root: str,
    library_versions: dict[str, str],
    executed_at: str | None = None,
    code_commit: str | None = None,
    run_id: str | None = None,
    published_artifact_hashes: dict[str, str] | None = None,
    validation: dict[str, Any] | None = None,
    decision: str = "not_published",
) -> dict[str, Any]:
    """Create the future execution record without writing it."""

    if executed_at is None:
        executed_at = datetime.now(timezone.utc).isoformat()
    if code_commit is None:
        try:
            code_commit = subprocess.run(
                ["git", "rev-parse", "HEAD"], check=True, capture_output=True, text=True
            ).stdout.strip()
        except (OSError, subprocess.CalledProcessError):
            code_commit = "unknown"
    return {
        "stage": "stage2_eda",
        "run_id": run_id,
        "executed_at": executed_at,
        "code_commit": code_commit,
        "inputs": input_identities,
        "parameters": parameters,
        "library_versions": library_versions,
        "output_root": output_root,
        "decision": decision,
        "published_artifact_hashes": published_artifact_hashes or {},
        "validation": validation or {},
        "publication_policy": "publicar atomicamente somente após validação; preservar runs anteriores em archive/<run_id>",
    }
