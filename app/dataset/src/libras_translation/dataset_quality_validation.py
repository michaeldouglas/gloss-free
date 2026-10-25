"""Provenance, quality decisions and validated manifest generation.

This module consumes the technical metadata JSON produced by
``metadata_validation``.  It deliberately keeps the raw dataset out of the
write path: reports and manifests are derived artifacts only.
"""

from __future__ import annotations

import csv
import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any

from .metadata_validation import filesystem_key_column


SEVERITIES = ("CRITICAL", "ERROR", "WARNING", "INFO")
_VIDEO_SUFFIXES = {".avi", ".flv", ".m4v", ".mkv", ".mov", ".mp4", ".webm", ".wmv"}
_REASON_COLUMNS = ("reason", "error", "motivo", "message", "mensagem", "status")
_MISSING_REASON_TOKENS = ("missing", "not found", "absent", "ausente", "não encontrado", "nao encontrado")
_UNREADABLE_REASON_TOKENS = ("corrupt", "invalid", "unreadable", "ilegível", "ilegivel", "corromp")


def _normalise_name(value: Any) -> str:
    text = str(value or "").strip().replace("\\", "/")
    while text.startswith("./"):
        text = text[2:]
    return text


def _name_key(value: Any) -> str:
    return _normalise_name(value).casefold()


def _read_csv(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        return [
            {**row, "_source_file": path.name, "_row_number": index}
            for index, row in enumerate(reader, start=2)
        ]


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames: list[str] = []
    for row in rows:
        for key in row:
            if key not in fieldnames:
                fieldnames.append(key)
    if not fieldnames:
        fieldnames = ["dataset", "severity", "code", "message"]
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def _json_dump(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str) + "\n", encoding="utf-8")


def _as_float(value: Any) -> float | None:
    try:
        return None if value in (None, "") else float(value)
    except (TypeError, ValueError):
        return None


def _is_zero(value: Any) -> bool:
    parsed = _as_float(value)
    return parsed == 0 if parsed is not None else False


def _reason(row: dict[str, Any], *, file_exists: bool, probe_status: str | None) -> tuple[str, bool | None, str]:
    explicit = next(
        (str(row.get(column, "")).strip() for column in _REASON_COLUMNS if str(row.get(column, "")).strip()),
        None,
    )
    if explicit:
        lowered = explicit.casefold()
        if any(token in lowered for token in _MISSING_REASON_TOKENS):
            consistent = not file_exists
            return "missing_file", consistent, "motivo explícito indica arquivo ausente"
        if any(token in lowered for token in _UNREADABLE_REASON_TOKENS):
            consistent = file_exists and probe_status not in {"ok", "partial"}
            return "unreadable_file", consistent, "motivo explícito indica arquivo ilegível/corrompido"
        return "explicit_unknown", None, "motivo explícito não pôde ser classificado automaticamente"

    if all(_is_zero(row.get(column)) for column in ("width", "height", "fps")):
        if not file_exists:
            return "missing_file_inferred", True, "width, height e fps zerados; arquivo ausente"
        if probe_status not in {"ok", "partial"}:
            return "unreadable_file_inferred", True, "width, height e fps zerados; inspeção falhou"
        return "missing_file_inferred", False, "CSV indica erro, mas o arquivo existe e é legível"

    return "unknown", None, "error.csv não possui motivo explícito nem marcador técnico suficiente"


def _filename_check(dataset: str, video_name: str, record: dict[str, Any] | None) -> tuple[bool | None, str]:
    """Validate the known V-LIBRASIL convention without guessing MINDS."""

    normalised = _normalise_name(video_name)
    path = PurePosixPath(normalised)
    if not normalised:
        return False, "video_name vazio"
    if path.suffix.casefold() not in _VIDEO_SUFFIXES:
        return False, "extensão de vídeo não suportada"

    if dataset != "v-librasil-raw":
        return None, "extensão válida; chave física MINDS é video_id"

    expected_class = _normalise_name((record or {}).get("class"))
    expected_user = str((record or {}).get("user_id") or "").strip()
    if dataset == "v-librasil-raw":
        if "_" not in path.stem:
            return False, "nome não contém separador class_user_id"
        filename_class, filename_user = path.stem.rsplit("_", 1)
        if not filename_class or not re.fullmatch(r"Articulador\d+", filename_user):
            return False, "user_id no nome não segue Articulador + número"
        if expected_class and _name_key(filename_class) != _name_key(expected_class):
            return False, f"class do nome={filename_class!r} difere da registrada={expected_class!r}"
        if expected_user and filename_user != expected_user:
            return False, f"user_id do nome={filename_user!r} difere da registrada={expected_user!r}"
        return True, "convenção class_user_id válida"

    # MINDS-Libras has no convention declared by the current project contract.
    # We still validate the physical extension and compare identifiers when the
    # source record exposes them, while making the uncertainty explicit.
    if expected_class or expected_user:
        if "_" not in path.stem:
            return None, "extensão válida; convenção MINDS não especificada"
        filename_class, filename_user = path.stem.rsplit("_", 1)
        if expected_class and _name_key(filename_class) != _name_key(expected_class):
            return False, f"class do nome={filename_class!r} difere da registrada={expected_class!r}"
        if expected_user and filename_user != expected_user:
            return False, f"user_id do nome={filename_user!r} difere da registrada={expected_user!r}"
    return None, "extensão válida; convenção MINDS não especificada"


def _descriptive_name_check(record: dict[str, Any]) -> tuple[str, str]:
    """Classify the relation between MINDS physical and descriptive names."""

    video_id = _normalise_name(record.get("video_id"))
    video_name = _normalise_name(record.get("video_name"))
    if not video_id or not video_name:
        return "missing", "video_id ou video_name ausente"
    if _name_key(video_id) == _name_key(video_name):
        return "same", "video_name é igual ao video_id"

    id_stem = PurePosixPath(video_id).stem
    name_stem = PurePosixPath(video_name).stem
    id_without_numeric_prefix = re.sub(r"^\d+", "", id_stem)
    if _name_key(id_without_numeric_prefix) == _name_key(name_stem.replace("_", "")):
        return "deterministic_prefix_and_separator", "video_id adiciona prefixo numérico e remove o separador de video_name"

    expected_class = _name_key(record.get("class"))
    expected_user = _name_key(record.get("user_id"))
    name_key = _name_key(name_stem)
    if expected_class and expected_user and expected_class in name_key and expected_user in name_key:
        return "components_consistent", "video_name contém class e user_id registrados"
    return "inconsistent", "video_name não pôde ser relacionado deterministicamente a video_id, class e user_id"


def _metadata_map(payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for item in payload.get("results", []):
        key = _name_key(item.get("input", {}).get("relative_path"))
        if key:
            result[key] = item
    return result


def _physical_files(videos_root: Path) -> tuple[dict[str, list[Path]], list[dict[str, Any]]]:
    by_key: dict[str, list[Path]] = defaultdict(list)
    for path in sorted(videos_root.rglob("*")) if videos_root.is_dir() else []:
        if path.is_file() and path.suffix.casefold() in _VIDEO_SUFFIXES:
            relative = path.relative_to(videos_root).as_posix()
            by_key[_name_key(relative)].append(path)
    duplicates = [
        {"relative_path": paths[0].relative_to(videos_root).as_posix(), "count": len(paths)}
        for paths in by_key.values()
        if len(paths) > 1
    ]
    return by_key, duplicates


def _severity_max(severities: list[str]) -> str | None:
    for severity in SEVERITIES:
        if severity in severities:
            return severity
    return None


def generate_validation_artifacts(
    *,
    dataset: str,
    dataset_root: Path,
    metadata_payload: dict[str, Any],
    output_root: Path,
    metadata_json: Path | None = None,
) -> dict[str, Any]:
    """Validate provenance and write reports plus one immutable-derived manifest."""

    dataset_root = Path(dataset_root).resolve()
    output_root = Path(output_root).resolve()
    annotations_path = dataset_root / "annotations.csv"
    exceptions_path = dataset_root / "error.csv"
    key_column = filesystem_key_column(dataset)
    annotations = _read_csv(annotations_path)
    exceptions = _read_csv(exceptions_path)
    metadata = _metadata_map(metadata_payload)
    physical, physical_duplicates = _physical_files(dataset_root / "videos")

    issues: list[dict[str, Any]] = []
    row_issues: dict[str, list[dict[str, Any]]] = defaultdict(list)
    reason_by_key: dict[str, tuple[str, bool | None, str]] = {}
    provenance_counts = Counter()

    def add_issue(
        severity: str,
        code: str,
        message: str,
        *,
        key: str = "",
        video_name: str = "",
        source: str = "",
        row_number: int | None = None,
        evidence: str = "",
    ) -> None:
        issue = {
            "dataset": dataset,
            "severity": severity,
            "code": code,
            "video_name": video_name,
            "source": source,
            "row_number": row_number,
            "message": message,
            "evidence": evidence,
        }
        issues.append(issue)
        if key:
            row_issues[key].append(issue)

    if not annotations_path.is_file():
        add_issue("CRITICAL", "annotations_missing", "annotations.csv não existe", source="annotations.csv")

    if dataset == "v-librasil-raw" and not exceptions_path.is_file():
        add_issue(
            "CRITICAL",
            "error_csv_missing",
            "V-LIBRASIL exige error.csv como parte da proveniência do dataset",
            source="error.csv",
        )
    elif not exceptions_path.is_file():
        add_issue("INFO", "error_csv_absent", "dataset não possui error.csv; nenhuma exceção foi reconciliada", source="error.csv")

    annotation_by_key: dict[str, list[dict[str, Any]]] = defaultdict(list)
    exception_by_key: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in annotations:
        annotation_by_key[_name_key(row.get(key_column))].append(row)
    for row in exceptions:
        exception_by_key[_name_key(row.get(key_column))].append(row)

    descriptive_name_status_by_key: dict[str, tuple[str, str]] = {}
    descriptive_name_counts: Counter[str] = Counter()
    if dataset == "minds-libras-raw":
        for key, rows in annotation_by_key.items():
            if rows:
                relation = _descriptive_name_check(rows[0])
                descriptive_name_status_by_key[key] = relation
                descriptive_name_counts[relation[0]] += 1

    for key, rows in annotation_by_key.items():
        if key and len(rows) > 1:
            add_issue("CRITICAL", "duplicate_annotation", f"{key_column} aparece mais de uma vez em annotations.csv", key=key, video_name=rows[0].get("video_name", ""), source="annotations.csv", evidence=f"{len(rows)} ocorrências")
    for key, rows in exception_by_key.items():
        if key and len(rows) > 1:
            add_issue("CRITICAL", "duplicate_exception", f"{key_column} aparece mais de uma vez em error.csv", key=key, video_name=rows[0].get("video_name", ""), source="error.csv", evidence=f"{len(rows)} ocorrências")

    for duplicate in physical_duplicates:
        add_issue("CRITICAL", "duplicate_physical_name", "mais de um arquivo físico corresponde ao mesmo caminho lógico", video_name=duplicate["relative_path"], source="videos/", evidence=f"{duplicate['count']} arquivos")

    all_keys = set(annotation_by_key) | set(exception_by_key) | set(physical) | set(metadata)
    for key in sorted(all_keys):
        annotation = annotation_by_key.get(key, [None])[0]
        exception = exception_by_key.get(key, [None])[0]
        record = annotation or exception or {}
        meta_item = metadata.get(key, {})
        video_name = str(
            record.get("video_name")
            or meta_item.get("input", {}).get("relative_path")
            or (next(iter(physical[key]), None).relative_to(dataset_root / "videos").as_posix() if physical.get(key) else "")
        )
        probe = meta_item.get("probe", {}) if isinstance(meta_item, dict) else {}
        comparison = meta_item.get("comparison", {}) if isinstance(meta_item, dict) else {}
        file_exists = bool(physical.get(key))
        probe_status = probe.get("status")

        if annotation and not file_exists and not exception:
            provenance_counts["silent_missing_files"] += 1
            add_issue("ERROR", "silent_missing_file", "registro de annotations.csv não possui arquivo em videos/ e não está em error.csv", key=key, video_name=video_name, source="annotations.csv", row_number=annotation.get("_row_number"))
        if annotation and file_exists and probe_status == "error":
            add_issue("ERROR", "unreadable_video", "arquivo existe, mas a inspeção técnica falhou", key=key, video_name=video_name, source="videos/", evidence=str(probe.get("error", {})))

        if exception:
            provenance_counts["error_rows"] += 1
            provenance_counts["error_in_annotations"] += int(bool(annotation))
            provenance_counts["error_with_physical_file"] += int(file_exists)
            provenance_counts["error_missing_file"] += int(not file_exists)
            if not annotation:
                add_issue("ERROR", "exception_not_in_annotations", "item de error.csv não aparece em annotations.csv", key=key, video_name=video_name, source="error.csv", row_number=exception.get("_row_number"))
            reason_kind, reason_consistent, reason_note = _reason(exception, file_exists=file_exists, probe_status=probe_status)
            reason_by_key[key] = (reason_kind, reason_consistent, reason_note)
            if reason_consistent is False:
                add_issue("ERROR", "exception_reason_inconsistent", reason_note, key=key, video_name=video_name, source="error.csv", row_number=exception.get("_row_number"), evidence=reason_kind)
            elif reason_consistent is None:
                add_issue("WARNING", "exception_reason_unknown", reason_note, key=key, video_name=video_name, source="error.csv", row_number=exception.get("_row_number"), evidence=reason_kind)
            if not file_exists:
                add_issue("ERROR", "known_missing_file", "arquivo listado em error.csv não existe em videos/", key=key, video_name=video_name, source="error.csv", row_number=exception.get("_row_number"), evidence="ausência explicitamente registrada")
            elif probe_status == "error":
                add_issue("ERROR", "known_unreadable_file", "arquivo listado em error.csv existe, mas não é legível pelo ffprobe", key=key, video_name=video_name, source="error.csv", row_number=exception.get("_row_number"))

        if file_exists and not annotation and not exception:
            add_issue("ERROR", "unregistered_physical_file", "arquivo físico não aparece em annotations.csv nem em error.csv", key=key, video_name=video_name, source="videos/")

        if comparison.get("overall_status") == "mismatch":
            add_issue("WARNING", "metadata_mismatch", "metadados declarados diferem dos valores observados", key=key, video_name=video_name, source="annotations.csv" if annotation else "error.csv", evidence=json.dumps(comparison, ensure_ascii=False, default=str))
        elif comparison.get("overall_status") == "inconclusive":
            add_issue("WARNING", "metadata_inconclusive", "metadados não puderam ser comparados completamente", key=key, video_name=video_name, source="metadata_validation.json", evidence=json.dumps(comparison, ensure_ascii=False, default=str))

        if dataset == "minds-libras-raw":
            filename_valid, filename_note = None, "chave física MINDS validada por video_id"
            if annotation:
                descriptive_status, descriptive_note = descriptive_name_status_by_key.get(
                    key, ("missing", "video_id ou video_name ausente")
                )
                if descriptive_status == "missing":
                    add_issue("ERROR", "descriptive_name_missing", descriptive_note, key=key, video_name=video_name, source="annotations.csv", row_number=annotation.get("_row_number"))
                elif descriptive_status == "inconsistent":
                    add_issue("WARNING", "descriptive_name_inconsistent", descriptive_note, key=key, video_name=video_name, source="annotations.csv", row_number=annotation.get("_row_number"))
        else:
            filename_valid, filename_note = _filename_check(dataset, video_name, record)
            if filename_valid is False:
                mismatch = "class do nome" in filename_note or "user_id do nome" in filename_note
                add_issue("CRITICAL" if mismatch else "ERROR", "filename_invalid", filename_note, key=key, video_name=video_name, source=record.get("_source_file", ""), row_number=record.get("_row_number"))
            elif filename_valid is None:
                add_issue("INFO", "filename_convention_undefined", filename_note, key=key, video_name=video_name, source=record.get("_source_file", ""), row_number=record.get("_row_number"))

    codec_counts = Counter(
        str(item.get("probe", {}).get("codec"))
        for item in metadata.values()
        if item.get("probe", {}).get("codec")
    )
    if len(codec_counts) > 1:
        add_issue(
            "INFO",
            "multiple_codecs",
            "o dataset contém mais de um codec de vídeo; a característica deve ser considerada no preparo",
            source="metadata_validation.json",
            evidence=json.dumps(dict(codec_counts), ensure_ascii=False),
        )

    if dataset == "v-librasil-raw" and not exceptions:
        add_issue("CRITICAL", "error_csv_empty", "error.csv existe, mas não possui registros de proveniência", source="error.csv")

    manifest_rows: list[dict[str, Any]] = []
    for key in sorted(all_keys):
        annotation = annotation_by_key.get(key, [None])[0]
        exception = exception_by_key.get(key, [None])[0]
        record = annotation or exception or {}
        meta_item = metadata.get(key, {})
        probe = meta_item.get("probe", {}) if isinstance(meta_item, dict) else {}
        comparison = meta_item.get("comparison", {}) if isinstance(meta_item, dict) else {}
        paths = physical.get(key, [])
        file_exists = bool(paths)
        manifest_video_name = str(
            record.get("video_name")
            or meta_item.get("input", {}).get("relative_path")
            or (paths[0].relative_to(dataset_root / "videos").as_posix() if paths else "")
        )
        if dataset == "minds-libras-raw":
            filename_valid, filename_note = None, "chave física MINDS validada por video_id"
            descriptive_status, descriptive_note = descriptive_name_status_by_key.get(
                key, ("missing", "video_id ou video_name ausente")
            )
        else:
            filename_valid, filename_note = _filename_check(dataset, manifest_video_name, record)
            descriptive_status, descriptive_note = None, None
        scoped_issues = row_issues.get(key, [])
        severity = _severity_max([issue["severity"] for issue in scoped_issues])
        status = severity.lower() if severity else "valid"
        if exception and not file_exists and severity == "ERROR":
            status = "excluded_error"
        row: dict[str, Any] = {
            key_name: value
            for key_name, value in record.items()
            if not key_name.startswith("_")
        }
        row.update(
            {
                "dataset": dataset,
                "filesystem_key_column": key_column,
                "filesystem_key": record.get(key_column) or (paths[0].name if paths else ""),
                "video_name": manifest_video_name,
                "relative_path": str(meta_item.get("input", {}).get("relative_path") or (paths[0].relative_to(dataset_root / "videos").as_posix() if paths else record.get("video_name", ""))),
                "source_csv": ";".join(source for source, present in (("annotations.csv", bool(annotation)), ("error.csv", bool(exception))) if present),
                "error_in_annotations": bool(exception and annotation),
                "error_file_exists": bool(exception and file_exists),
                "error_reason_kind": reason_by_key.get(key, (None, None, None))[0],
                "error_reason_consistent": reason_by_key.get(key, (None, None, None))[1],
                "actual_width": probe.get("actual_width"),
                "actual_height": probe.get("actual_height"),
                "actual_fps": probe.get("actual_fps"),
                "actual_frame_count": probe.get("actual_frame_count"),
                "actual_duration": probe.get("actual_duration_seconds"),
                "codec": probe.get("codec"),
                "file_exists": file_exists,
                "file_readable": bool(file_exists and probe.get("status") in {"ok", "partial"}),
                "filename_valid": filename_valid,
                "descriptive_name_status": descriptive_status,
                "descriptive_name_note": descriptive_note,
                "metadata_valid": bool(file_exists and probe.get("status") in {"ok", "partial"} and comparison.get("overall_status") == "match"),
                "validation_status": status,
                "validation_notes": "; ".join(issue["message"] for issue in scoped_issues) or filename_note,
            }
        )
        manifest_rows.append(row)

    reports_dir = output_root / "reports"
    manifests_dir = output_root / "manifests"
    report_path = reports_dir / "metadata_validation_report.md"
    issues_path = reports_dir / "metadata_issues.csv"
    summary_path = reports_dir / "metadata_summary.json"
    manifest_name = "v_librasil_validated.parquet" if dataset == "v-librasil-raw" else "minds_libras_validated.parquet" if dataset == "minds-libras-raw" else f"{dataset.replace('-', '_')}_validated.parquet"
    manifest_path = manifests_dir / manifest_name

    _write_csv(issues_path, issues)
    severity_counts = Counter(issue["severity"] for issue in issues)
    decision = "GO" if not any(severity_counts.get(severity, 0) for severity in ("CRITICAL", "ERROR")) else "NO-GO"
    annotation_keys = {key for key in annotation_by_key if key}
    physical_keys = set(physical)
    key_reconciliation = {
        "filesystem_key_column": key_column,
        "csv_records": len(annotations),
        "physical_files": sum(len(paths) for paths in physical.values()),
        "csv_key_unique": len(annotation_keys) == len(annotations),
        "csv_key_duplicates": sum(max(len(rows) - 1, 0) for key, rows in annotation_by_key.items() if key),
        "physical_key_duplicates": sum(max(item["count"] - 1, 0) for item in physical_duplicates),
        "matched": len(annotation_keys & physical_keys),
        "missing": len(annotation_keys - physical_keys),
        "extra": len(physical_keys - annotation_keys),
    }
    summary = {
        "schema_version": "dataset-validation-summary.v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "dataset": dataset,
        "decision": decision,
        "source": {
            "dataset_root": str(dataset_root),
            "annotations_csv": str(annotations_path),
            "error_csv": str(exceptions_path) if exceptions_path.is_file() else None,
            "metadata_validation": str(metadata_json.resolve()) if metadata_json else None,
        },
        "counts": {
            "annotations": len(annotations),
            "exceptions": len(exceptions),
            "physical_videos": sum(len(paths) for paths in physical.values()),
            "manifest_rows": len(manifest_rows),
            "issues": len(issues),
            "by_severity": {severity: severity_counts.get(severity, 0) for severity in SEVERITIES},
            "provenance": dict(provenance_counts),
        },
        "key_reconciliation": key_reconciliation,
        "video_name_analysis": {
            "relation_counts": dict(descriptive_name_counts),
            "rule": "video_id sem prefixo numérico e video_name sem underscores são comparados após normalização; class e user_id são conferidos como componentes",
        } if dataset == "minds-libras-raw" else None,
        "artifacts": {
            "report": str(report_path),
            "issues": str(issues_path),
            "manifest": str(manifest_path),
        },
    }
    _json_dump(summary_path, summary)

    report_lines = [
        f"# Validação de metadados e proveniência — {dataset}",
        "",
        f"**Decisão: {decision}**",
        "",
        "A decisão é `NO-GO` quando existe pelo menos um problema `CRITICAL` ou `ERROR`. "
        "Registros conhecidos em `error.csv` permanecem explícitos e não são promovidos a dados válidos.",
        "",
        "## Evidências",
        "",
        f"- annotations.csv: {len(annotations)} registros",
        f"- error.csv: {len(exceptions)} registros",
        f"- vídeos físicos: {sum(len(paths) for paths in physical.values())}",
        f"- linhas no manifest validado: {len(manifest_rows)}",
        f"- chave física CSV: `{key_column}`",
        f"- chaves correspondentes: {key_reconciliation['matched']}",
        f"- chaves ausentes: {key_reconciliation['missing']}",
        f"- arquivos extras: {key_reconciliation['extra']}",
        "",
        "| Severidade | Quantidade |",
        "|---|---:|",
    ]
    report_lines.extend(f"| {severity} | {severity_counts.get(severity, 0)} |" for severity in SEVERITIES)
    report_lines.extend(["", "## Principais problemas", ""])
    if issues:
        report_lines.extend(
            f"- **{issue['severity']}** `{issue['code']}` — {issue['message']}"
            + (f" ({issue['video_name']})" if issue["video_name"] else "")
            for issue in issues[:100]
        )
        if len(issues) > 100:
            report_lines.append(f"- … {len(issues) - 100} problemas adicionais estão em `metadata_issues.csv`.")
    else:
        report_lines.append("Nenhum problema foi encontrado.")
    report_lines.extend(
        [
            "",
            "## Artefatos",
            "",
            f"- `{issues_path.name}`: evidências linha a linha.",
            f"- `{summary_path.name}`: contagens e decisão reproduzível.",
            f"- `{manifest_path.name}`: manifest derivado, sem alteração das entradas em `data/raw/`.",
        ]
    )
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(report_lines) + "\n", encoding="utf-8")

    try:
        import pandas as pd

        manifests_dir.mkdir(parents=True, exist_ok=True)
        pd.DataFrame(manifest_rows).to_parquet(manifest_path, index=False)
    except ImportError as exc:  # pragma: no cover - exercised by environment setup
        raise RuntimeError("A geração de manifests Parquet requer pandas e pyarrow.") from exc

    return {"summary": summary, "issues": issues, "manifest_rows": manifest_rows}


def generate_validation_artifacts_from_file(
    *, dataset: str, dataset_root: Path, metadata_json: Path, output_root: Path
) -> dict[str, Any]:
    """Load the technical JSON and generate the quality artifacts."""

    payload = json.loads(Path(metadata_json).read_text(encoding="utf-8"))
    return generate_validation_artifacts(
        dataset=dataset,
        dataset_root=dataset_root,
        metadata_payload=payload,
        output_root=output_root,
        metadata_json=Path(metadata_json),
    )
