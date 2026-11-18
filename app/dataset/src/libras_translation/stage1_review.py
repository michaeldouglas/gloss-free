"""Read-only tabular review of the V-LIBRASIL Stage 1 closeout."""

from __future__ import annotations

import csv
import math
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable

from .metadata_validation import normalize_filename_key as normalize_stage1_key

EXPECTED_ANNOTATIONS = 4_086
FPS_DEFAULT_TOLERANCE = 0.01
VIDEO_SUFFIXES = {".avi", ".flv", ".m4v", ".mkv", ".mov", ".mp4", ".webm", ".wmv"}
REQUIRED_COLUMNS = ("video_id", "video_name", "class", "user_id", "width", "height", "fps", "url_page", "url_download")
SPECIAL_NAME_FAMILIES = (r"Frente\Á Frente_Articulador", 'Cérebro (de "ervilha")_Articulador', "O quê?_Articulador")
DOCUMENTED_EXCEPTIONS = ("Congelar_Articulador3.mp4", "Criança_Articulador3.mp4", "Poesia_Articulador2.mp4")


def _present(value: Any) -> bool:
    return value is not None and not (isinstance(value, float) and math.isnan(value)) and str(value).strip() != ""


def _number(value: Any) -> float | None:
    if not _present(value):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def _bool(value: Any) -> bool:
    return value is True or str(value).casefold() in {"true", "1", "yes", "ok"}


def _is_url(value: Any) -> bool:
    return str(value or "").strip().casefold().startswith(("http://", "https://"))


def _read_csv(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return [{**row, "_row_number": number} for number, row in enumerate(csv.DictReader(stream), 2)]


def _row_source(row: dict[str, Any]) -> str:
    return str(row.get("source_csv") or row.get("_source_file") or "")


def _row_key(row: dict[str, Any]) -> str:
    return normalize_stage1_key(row.get("video_name") or row.get("filesystem_key"))


def _technical_by_key(payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for item in payload.get("results", []) or []:
        if not isinstance(item, dict):
            continue
        csv_record, input_info = item.get("csv") or {}, item.get("input") or {}
        for candidate in (csv_record.get("video_name"), input_info.get("relative_path"), input_info.get("filename")):
            key = normalize_stage1_key(candidate)
            if key:
                result.setdefault(key, item)
    return result


def _issue_counts(summary: dict[str, Any]) -> dict[str, Any]:
    counts = summary.get("counts") or {}
    return {"issues_total": int(counts.get("issues", 0) or 0), "affected_files": int(counts.get("affected_files", 0) or 0), "affected_annotations": int(counts.get("affected_annotations", 0) or 0), "by_severity": dict(counts.get("by_severity") or {})}


def _fps_review(rows: list[dict[str, Any]], technical: dict[str, dict[str, Any]], tolerance: float) -> dict[str, Any]:
    counts = Counter({key: 0 for key in ("csv_fps_matches_actual_fps", "csv_fps_matches_actual_frame_count", "exclusive_actual_fps", "exclusive_actual_frame_count", "matches_both", "matches_neither", "inconclusive", "invalid_declared_values", "evaluable_both_hypotheses")})
    rate_sources, frame_sources = Counter(), Counter()
    for row in rows:
        item = technical.get(_row_key(row), {})
        comparison, probe = item.get("comparison") or {}, item.get("probe") or {}
        rate_status, frame_status = comparison.get("fps_rate_status"), comparison.get("fps_frame_count_status")
        rate_sources[str(probe.get("actual_fps_source") or "unknown")] += 1
        frame_sources[str(probe.get("actual_frame_count_source") or "unknown")] += 1
        if rate_status == frame_status == "match": counts["matches_both"] += 1
        elif rate_status == "match" and frame_status == "mismatch": counts["exclusive_actual_fps"] += 1
        elif frame_status == "match" and rate_status == "mismatch": counts["exclusive_actual_frame_count"] += 1
        elif rate_status == frame_status == "mismatch": counts["matches_neither"] += 1
        elif rate_status == "invalid" or frame_status == "invalid": counts["invalid_declared_values"] += 1
        else: counts["inconclusive"] += 1
        counts["csv_fps_matches_actual_fps"] += int(rate_status == "match")
        counts["csv_fps_matches_actual_frame_count"] += int(frame_status == "match")
        counts["evaluable_both_hypotheses"] += int(rate_status in {"match", "mismatch"} and frame_status in {"match", "mismatch"})
    total = len(rows)
    coverage = counts["evaluable_both_hypotheses"] / total if total else 0.0
    rate_exclusive, frame_exclusive = counts["exclusive_actual_fps"], counts["exclusive_actual_frame_count"]
    candidate = "actual_fps" if rate_exclusive > frame_exclusive else "actual_frame_count" if frame_exclusive > rate_exclusive else "ambiguous" if counts["matches_both"] else "undetermined"
    exclusive = max(rate_exclusive, frame_exclusive)
    if total and coverage == 1 and exclusive == total and not any(counts[key] for key in ("matches_both", "matches_neither", "inconclusive", "invalid_declared_values")): confidence = "high"
    elif total and coverage >= 0.95 and exclusive / total >= 0.95 and rate_exclusive != frame_exclusive: confidence = "moderate"
    else: confidence = "low/undetermined"
    winner = candidate if confidence in {"high", "moderate"} else "undetermined"
    return {"tolerance": tolerance, "total_annotations": total, "coverage": coverage, "confidence": confidence, "hypothesis_winner": winner, "candidate_winner": candidate, "rate_source_counts": dict(rate_sources), "frame_count_source_counts": dict(frame_sources), "confidence_thresholds": {"high_coverage": 1.0, "high_exclusive": 1.0, "moderate_coverage": 0.95, "moderate_exclusive": 0.95}, **dict(counts), "confidence_rule": "high requires 100% dual coverage and exclusive match; moderate requires >=95% dual coverage and exclusive match, strictly exclusive; otherwise low/undetermined"}


def _axis(title: str, status: str, justification: str, evidence: list[str], refs: list[str]) -> dict[str, Any]:
    return {"id": title.split(".", 1)[0], "title": title, "status": status, "justification": justification, "evidence": evidence, "specification_mapping": refs}


def _integrity_proven(integrity: Any) -> bool:
    if not isinstance(integrity, dict): return False
    required_pairs = (("annotations_before", "annotations_after"), ("error_before", "error_after"), ("video_inventory_before", "video_inventory_after"))
    if all(before in integrity and after in integrity for before, after in required_pairs):
        return all(integrity[before] == integrity[after] for before, after in required_pairs)
    before, after = integrity.get("before"), integrity.get("after")
    if isinstance(before, dict) and isinstance(after, dict):
        if {"annotations.csv", "error.csv"} <= before.keys() and {"annotations.csv", "error.csv"} <= after.keys():
            return (all(before[name] == after[name] for name in ("annotations.csv", "error.csv"))
                    and "video_inventory_before" in integrity and "video_inventory_after" in integrity
                    and integrity["video_inventory_before"] == integrity["video_inventory_after"])
        required = ("annotations", "error", "video_inventory")
        return all(name in before and name in after and before[name] == after[name] for name in required)
    before, after = integrity.get("source_before"), integrity.get("source_after")
    if isinstance(before, dict) and isinstance(after, dict):
        required = ("annotations.csv", "error.csv", "video_inventory")
        return all(name in before and name in after and before[name] == after[name] for name in required)
    return False


def build_stage1_review(dataset_root: Path, technical_payload: dict[str, Any], quality_summary: dict[str, Any], manifest_rows: Iterable[dict[str, Any]]) -> dict[str, Any]:
    """Review derived V-LIBRASIL artifacts while reading tabular names only."""
    root = Path(dataset_root).resolve()
    annotations, exceptions = _read_csv(root / "annotations.csv"), _read_csv(root / "error.csv")
    physical_paths = [path for path in sorted((root / "videos").rglob("*")) if path.is_file() and path.suffix.casefold() in VIDEO_SUFFIXES]
    physical_by_key: dict[str, list[Path]] = defaultdict(list)
    for path in physical_paths: physical_by_key[normalize_stage1_key(path.name)].append(path)
    annotation_by_name: dict[str, list[dict[str, Any]]] = defaultdict(list)
    annotation_by_id: dict[str, list[dict[str, Any]]] = defaultdict(list)
    class_user_by_name: dict[str, set[tuple[str, str]]] = defaultdict(set)
    for row in annotations:
        annotation_by_name[normalize_stage1_key(row.get("video_name"))].append(row)
        annotation_by_id[normalize_stage1_key(row.get("video_id"))].append(row)
        class_user_by_name[normalize_stage1_key(row.get("video_name"))].add((normalize_stage1_key(row.get("class")), normalize_stage1_key(row.get("user_id"))))
    technical = _technical_by_key(technical_payload)
    manifest = [dict(row) for row in manifest_rows]
    manifest_by_name = {normalize_stage1_key(row.get("video_name")): row for row in manifest if "annotations.csv" in _row_source(row).casefold()}
    annotation_keys = [normalize_stage1_key(row.get("video_name")) for row in annotations]
    collisions = {"video_name": {key: len(value) for key, value in annotation_by_name.items() if key and len(value) > 1}, "video_id": {key: len(value) for key, value in annotation_by_id.items() if key and len(value) > 1}, "physical": {key: len(value) for key, value in physical_by_key.items() if key and len(value) > 1}, "class_user_conflicts": {key: sorted(values) for key, values in class_user_by_name.items() if len(values) > 1}}
    exception_keys = {normalize_stage1_key(row.get("video_name")) for row in exceptions}
    expected_exception_keys = {normalize_stage1_key(name) for name in DOCUMENTED_EXCEPTIONS}
    extra_keys = {key for key in physical_by_key if key not in annotation_by_name and key not in exception_keys}
    matched = sum(int(key and len(annotation_by_name[key]) == 1 and len(physical_by_key.get(key, [])) == 1) for key in annotation_keys)
    missing = sum(int(not physical_by_key.get(key)) for key in annotation_keys)
    duplicates = sum(max(len(value) - 1, 0) for value in annotation_by_name.values())
    fps_tolerance = float((technical_payload.get("run") or {}).get("fps_tolerance", FPS_DEFAULT_TOLERANCE))
    fps_analysis = _fps_review(annotations, technical, fps_tolerance)
    schema_issues: list[dict[str, Any]] = []
    metadata_match_count = technical_valid_count = dataset_valid_count = filename_invalid = 0
    filename_values = []
    for index, row in enumerate(annotations, 2):
        for column in REQUIRED_COLUMNS:
            if column not in row or not _present(row.get(column)): schema_issues.append({"row": index, "column": column, "kind": "missing_or_null"})
        for column in ("width", "height", "fps"):
            value = _number(row.get(column))
            if value is None: schema_issues.append({"row": index, "column": column, "kind": "invalid_type"})
            elif value <= 0: schema_issues.append({"row": index, "column": column, "kind": "non_positive"})
        for column in ("url_page", "url_download"):
            if not _is_url(row.get(column)): schema_issues.append({"row": index, "column": column, "kind": "invalid_url"})
        key = normalize_stage1_key(row.get("video_name"))
        derived = manifest_by_name.get(key, {})
        item = technical.get(key, {})
        comparison, probe = item.get("comparison") or {}, item.get("probe") or {}
        metadata_match = derived.get("metadata_match") or ("match" if comparison.get("width_status") == comparison.get("height_status") == "match" and (comparison.get("fps_rate_status") == "match" or comparison.get("fps_frame_count_status") == "match") else "missing" if not physical_by_key.get(key) else "mismatch")
        metadata_match_count += int(metadata_match == "match")
        technical_ok = derived.get("technical_valid") if "technical_valid" in derived else bool(probe.get("status") in {"ok", "partial"} and all((_number(probe.get(field)) or 0) > 0 for field in ("actual_width", "actual_height", "actual_fps", "actual_duration_seconds")) and _present(probe.get("codec")))
        technical_valid_count += int(_bool(technical_ok))
        filename_state = derived.get("filename_valid")
        filename_values.append(filename_state)
        filename_invalid += int(filename_state is False)
        dataset_valid_count += int(_bool(derived.get("dataset_valid")))
    unreadable_files = sum(1 for key in physical_by_key if key in technical and (technical[key].get("probe") or {}).get("status") == "error")
    issue_counts = _issue_counts(quality_summary)
    severity = issue_counts["by_severity"]
    evidence = {"technical": "data/processed/metadata-validation/v-librasil-raw/metadata_validation.json", "quality_summary": "data/processed/metadata-validation/v-librasil-raw/reports/metadata_summary.json", "manifest": "data/processed/metadata-validation/v-librasil-raw/manifests/v_librasil_validated.parquet", "annotations": "data/raw/v-librasil-raw/annotations.csv", "filesystem": "data/raw/v-librasil-raw/videos/"}
    integrity_status = "PASS" if _integrity_proven(quality_summary.get("source_integrity")) else "PARTIAL"
    schema_status = "PASS" if not schema_issues else "PARTIAL"
    key_status = "FAIL" if any(collisions.values()) else "PASS"
    physical_valid_count = sum(int(key not in expected_exception_keys) for key in physical_by_key for _ in physical_by_key[key])
    recon_status = "PASS" if len(annotations) == EXPECTED_ANNOTATIONS and physical_valid_count == EXPECTED_ANNOTATIONS and matched == EXPECTED_ANNOTATIONS and not missing and not extra_keys and not duplicates else "FAIL"
    tech_status = "PASS" if technical_valid_count == len(annotations) and fps_analysis["confidence"] in {"high", "moderate"} else "PARTIAL" if technical_valid_count else "FAIL"
    filename_status = "FAIL" if any(value is False for value in filename_values) else "PASS" if filename_values and all(value is True for value in filename_values) else "PARTIAL"
    exception_status = exception_keys == expected_exception_keys and all(not physical_by_key.get(key) and key not in annotation_by_name for key in exception_keys)
    manifest_annotation_rows = [row for row in manifest if _row_source(row).casefold() == "annotations.csv"]
    manifest_consistent = len(manifest_annotation_rows) == len(annotations) and all(_row_source(row).casefold() == "annotations.csv" for row in manifest_annotation_rows) and Counter(normalize_stage1_key(row.get("video_name")) for row in manifest) == Counter(annotation_keys) and len(set(annotation_keys)) == len(annotation_keys)
    requirements = [
        _axis("1. Input reading and preservation", integrity_status, "Hashes tabulares e inventário físico antes/depois são iguais." if integrity_status == "PASS" else "A revisão não recebeu prova completa de igualdade antes/depois.", [evidence["annotations"], evidence["filesystem"]], ["FR-001", "FR-008", "SC-008"]),
        _axis("2. Schema and required values", schema_status, f"{len(schema_issues)} ocorrências em nove colunas obrigatórias.", [evidence["annotations"]], ["FR-001", "FR-003", "FR-006"]),
        _axis("3. Keys and uniqueness", key_status, f"Colisões: {sum(len(value) for value in collisions.values())}; video_name/video_id/class+user foram avaliados.", [evidence["annotations"], evidence["filesystem"]], ["FR-014", "FR-017", "SC-007"]),
        _axis("4. CSV/filesystem reconciliation", recon_status, f"{len(annotations)} anotações, {len(physical_paths)} arquivos físicos, {matched} correspondências, {missing} ausentes, {len(extra_keys)} extras e {duplicates} duplicados.", [evidence["annotations"], evidence["filesystem"]], ["FR-011", "FR-014", "SC-001", "SC-007"]),
        _axis("5. Technical metadata and FPS", tech_status, f"{technical_valid_count}/{len(annotations)} tecnicamente válidos; FPS {fps_analysis['confidence']}.", [evidence["technical"]], ["FR-002", "FR-007", "FR-011", "SC-001", "SC-003"]),
        _axis("6. Filename convention", filename_status, f"{filename_invalid} nomes inválidos; None permanece como PARTIAL.", [evidence["manifest"]], ["FR-017"]),
        _axis("7. Provenance and derived manifest", "FAIL" if not exception_status or not manifest_consistent or severity.get("CRITICAL") or severity.get("ERROR") else "PASS", f"Exceções observadas={exception_status}; manifest consistente={manifest_consistent}; {issue_counts['issues_total']} issues e {issue_counts['affected_files']} arquivos afetados.", [evidence["quality_summary"], evidence["manifest"]], ["FR-014", "FR-018", "SC-007", "SC-008"]),
    ]
    special = {}
    for family in SPECIAL_NAME_FAMILIES:
        prefix = normalize_stage1_key(family)
        names = [row.get("video_name") for row in annotations if normalize_stage1_key(row.get("video_name")).startswith(prefix)]
        special[family] = {"rows": len(names), "matched_unique": sum(int(len(physical_by_key.get(normalize_stage1_key(name), [])) == 1) for name in names), "normalized_prefix": prefix, "names": names[:20]}
    exceptions_detail = [{"video_name": row.get("video_name"), "observed": True, "in_annotations": normalize_stage1_key(row.get("video_name")) in annotation_by_name, "physical_file_exists": bool(physical_by_key.get(normalize_stage1_key(row.get("video_name")))), "documented": normalize_stage1_key(row.get("video_name")) in expected_exception_keys and normalize_stage1_key(row.get("video_name")) not in annotation_by_name and not physical_by_key.get(normalize_stage1_key(row.get("video_name")))} for row in exceptions]
    return {"schema_version": "v-librasil-stage1-review.v2", "dataset": "v-librasil-raw", "scope": "V-LIBRASIL Stage 1 closeout; pending human review; no global Stage 1 decision", "source_artifacts": evidence, "definitions": {"metadata_match": "unique physical correspondence, matching width/height and at least one FPS hypothesis", "technical_valid": "readable video stream with positive observed width, height, FPS, duration and codec; frame count can be unavailable", "dataset_valid": "required fields, unique correspondence, technical_valid, metadata_match=match and no blocking issue"}, "reconciliation": {"expected_annotations": EXPECTED_ANNOTATIONS, "annotations_recalculated": len(annotations), "physical_files_recalculated": len(physical_paths), "matched": matched, "missing": missing, "extras": len(extra_keys), "duplicates_after_normalization": duplicates, "collisions": collisions}, "validity_counts": {"metadata_match": metadata_match_count, "technical_valid": technical_valid_count, "dataset_valid": dataset_valid_count, "unreadable_files": unreadable_files}, "schema": {"required_columns": list(REQUIRED_COLUMNS), "issues": schema_issues}, "fps_analysis": fps_analysis, "fps": fps_analysis, "special_name_families": special, "issues": issue_counts, "documented_exceptions": exceptions_detail, "requirements": requirements, "review_axes": requirements}
