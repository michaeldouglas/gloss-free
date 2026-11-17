"""Coherent V-LIBRASIL generations with recoverable directory publication."""
from __future__ import annotations
import csv
import hashlib
import json
import os
import re
import shutil
import uuid
from datetime import datetime, timezone
from pathlib import Path
from decimal import Decimal
from collections import defaultdict, Counter

from .metadata_validation import (validate_dataset, normalize_filename_key, _parse_csv_int, _parse_csv_decimal,
    _status_for_expected_vs_actual, classify_fps_hypotheses, _summary, _flatten_result)
from .vlibrasil_validation import generate_vlibrasil_artifacts, write_json

TECHNICAL_FILES = ("metadata_validation.json", "video_metadata.csv", "metadata_comparison.csv",
                   "fps_hypotheses_summary.csv", "toolchain.json", "validation.log")

def digest(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024*1024), b""):
            h.update(block)
    return h.hexdigest()

def rederive_comparisons(payload, dataset_root):
    """Rejoin fresh observations to original annotations using final code."""
    groups = defaultdict(list)
    with (dataset_root / "annotations.csv").open(encoding="utf-8-sig", newline="") as stream:
        for row in csv.DictReader(stream):
            groups[normalize_filename_key(row.get("video_name"))].append(row)
    physical = defaultdict(list)
    for path in (dataset_root / "videos").rglob("*"):
        if path.is_file():
            physical[normalize_filename_key(path.name)].append(path)
    tolerance = Decimal(str(payload["run"]["fps_tolerance"]))
    for item in payload["results"]:
        key = normalize_filename_key(item["input"]["relative_path"].rsplit("/", 1)[-1])
        rows = groups.get(key, [])
        if len(rows) != 1 or len(physical.get(key, [])) != 1:
            item["comparison"].update(overall_status="duplicate" if len(rows) > 1 or len(physical.get(key, [])) > 1 else "error",
                                      fps_hypothesis="inconclusive")
            continue
        row, probe = rows[0], item["probe"]
        width, width_kind = _parse_csv_int(row.get("width"))
        height, height_kind = _parse_csv_int(row.get("height"))
        declared, declared_kind = _parse_csv_decimal(row.get("fps"))
        fields = probe.get("field_status", {})
        width_status = _status_for_expected_vs_actual(width, width_kind, probe.get("actual_width"), fields.get("width", "missing"))
        height_status = _status_for_expected_vs_actual(height, height_kind, probe.get("actual_height"), fields.get("height", "missing"))
        fps = classify_fps_hypotheses(declared, declared_kind, probe.get("actual_fps"), fields.get("fps", "missing"),
                                     probe.get("actual_frame_count"), fields.get("frame_count", "unavailable"), tolerance=tolerance)
        if probe.get("status") == "error": overall = "error"
        elif "mismatch" in {width_status, height_status} or fps["fps_hypothesis"] == "none": overall = "mismatch"
        elif "inconclusive" in {width_status, height_status, fps["fps_hypothesis"]} or "invalid" in {width_kind, height_kind, declared_kind}: overall = "inconclusive"
        else: overall = "match"
        item["csv"] = {**row, "_csv_source": "annotations.csv"}
        item["comparison"] = dict(csv_width=width, csv_height=height, csv_fps_raw=row.get("fps"), csv_fps_numeric=float(declared) if declared is not None else None,
                                  width_status=width_status, height_status=height_status, overall_status=overall, **fps)
    old_normalization = payload.get("summary", {}).get("normalization")
    payload["summary"] = _summary(payload["results"], dataset="v-librasil-raw", tolerance=float(tolerance))
    if old_normalization is not None:
        payload["summary"]["normalization"] = old_normalization
    payload["run"]["comparisons_rederived_at_utc"] = datetime.now(timezone.utc).isoformat()
    return payload

def video_inventory(dataset_root):
    rows = []
    for path in sorted((dataset_root / "videos").rglob("*")):
        if path.is_file():
            stat = path.stat()
            rows.append(dict(relative_path=path.relative_to(dataset_root).as_posix(),
                             size_bytes=stat.st_size, last_write_ns=stat.st_mtime_ns))
    return rows

def canonical_inventory(rows):
    """Normalize timestamp serialization only; never touch a source file."""
    result = []
    for row in rows:
        item = dict(row)
        if isinstance(item.get("last_write_utc"), str):
            item["last_write_utc"] = re.sub(
                r"\.(\d+)(Z|[+-]\d{2}:\d{2})$",
                lambda match: ("." + match.group(1).rstrip("0") if match.group(1).rstrip("0") else "") + match.group(2),
                item["last_write_utc"])
        result.append(item)
    return sorted(result, key=lambda row: row["relative_path"])

def inventory_digest(rows):
    value = json.dumps(canonical_inventory(rows), ensure_ascii=False, sort_keys=True).encode("utf-8")
    return hashlib.sha256(value).hexdigest()

def atomic_json(path, value):
    temp = path.with_name(path.name + "." + uuid.uuid4().hex + ".tmp")
    try:
        write_json(temp, value)
        os.replace(temp, path)
    finally:
        temp.unlink(missing_ok=True)

def publish_generation(staging, base_root, summary, *, generation_id):
    """Directory renames never expose mixed generations; a brief path gap is possible.

    Windows cannot atomically overwrite a nonempty directory. Move the previous
    generation aside, then rename the validated staging directory. Roll back
    synchronously on failure. This is not an ACID transaction across the registry.
    """
    staging, base_root = Path(staging).resolve(), Path(base_root).resolve()
    if staging.parent != base_root or not staging.name.startswith(".v-librasil-"):
        raise ValueError("Staging deve ser um diretório irmão controlado da saída canônica")
    canonical = base_root / "v-librasil-raw"
    history = base_root / "superseded" / ("v-librasil-" + generation_id)
    lock = base_root / ".v-librasil-publication.lock"
    descriptor = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    os.close(descriptor)
    previous = history / "previous-canonical"
    registry_path = base_root / "validation_runs.json"
    registry_bytes = registry_path.read_bytes() if registry_path.exists() else None
    legacy_moves = []
    promoted = False
    had_previous = canonical.exists()
    try:
        history.mkdir(parents=True)
        write_json(history / "SUPERSEDED.json", dict(dataset="v-librasil-raw",
                   superseded_by=generation_id, reason="Execução legada substituída pela normalização NFC/PUA/casefold; não canônica"))
        if had_previous:
            os.replace(canonical, previous)
        os.replace(staging, canonical)
        promoted = True
        # Retire only old root-level V-LIBRASIL evidence; never touch MINDS.
        old_summary = base_root / "reports/metadata_summary.json"
        if old_summary.exists() and json.loads(old_summary.read_text(encoding="utf-8")).get("dataset") == "v-librasil-raw":
            for filename in ("metadata_validation_report.md", "metadata_issues.csv", "metadata_summary.json"):
                path = base_root / "reports" / filename
                if not path.is_file():
                    continue
                destination = history / "legacy-root/reports" / path.name
                destination.parent.mkdir(parents=True, exist_ok=True)
                os.replace(path, destination)
                legacy_moves.append((destination, path))
        old_manifest = base_root / "manifests/v_librasil_validated.parquet"
        if old_manifest.exists():
            destination = history / "legacy-root/manifests" / old_manifest.name
            destination.parent.mkdir(parents=True, exist_ok=True)
            os.replace(old_manifest, destination)
            legacy_moves.append((destination, old_manifest))
        registry = json.loads(registry_bytes) if registry_bytes else {"schema_version": "validation-run-registry.v1", "runs": {}}
        registry.setdefault("runs", {})["v-librasil-raw"] = {
            "dataset": "v-librasil-raw", "status": "completed", "metadata_status": "completed",
            "quality_status": "completed", "decision": summary["decision"],
            "review_status": "pending_human_review", "logic_version": "v-librasil-stage1.nfc-pua.v1",
            "input_fingerprint": digest(canonical / "metadata_validation.json"),
            "metadata_artifacts": "data/processed/metadata-validation/v-librasil-raw",
            "quality_artifacts": "data/processed/metadata-validation/v-librasil-raw",
            "executed_at": summary["generated_at_utc"], "generation_id": generation_id,
            "reason": "Fechamento exclusivo V-LIBRASIL; revisão humana pendente; sem decisão global Etapa 1"}
        atomic_json(registry_path, registry)
    except BaseException:
        for origin, target in reversed(legacy_moves):
            if origin.exists():
                target.parent.mkdir(parents=True, exist_ok=True)
                os.replace(origin, target)
        if promoted and canonical.exists():
            os.replace(canonical, staging)
        if had_previous and previous.exists():
            os.replace(previous, canonical)
        if registry_bytes is not None:
            restore = registry_path.with_suffix(".rollback")
            restore.write_bytes(registry_bytes)
            os.replace(restore, registry_path)
        elif registry_path.exists():
            registry_path.unlink()
        raise
    finally:
        lock.unlink(missing_ok=True)
    return canonical

def finalize_vlibrasil(dataset_root, base_root, *, prepared_metadata=None,
                      ffprobe_executable="ffprobe", fps_tolerance=0.01, publish=True):
    import pandas as pd
    dataset_root, base_root = Path(dataset_root).resolve(), Path(base_root).resolve()
    base_root.mkdir(parents=True, exist_ok=True)
    if dataset_root.name != "v-librasil-raw":
        raise ValueError("Fechamento aceita exclusivamente v-librasil-raw")
    for protected in (dataset_root, dataset_root.parent):
        if base_root == protected or protected in base_root.parents:
            raise ValueError("Saídas não podem ficar no corpus bruto")
    generation = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex[:8]
    staging = base_root / (".v-librasil-" + generation)
    staging.mkdir()
    source_before = {name: digest(dataset_root / name) for name in ("annotations.csv", "error.csv")}
    inventory_before = video_inventory(dataset_root)
    if prepared_metadata is not None:
        prepared = Path(prepared_metadata).resolve()
        for name in TECHNICAL_FILES:
            shutil.copy2(prepared / name, staging / name)
        before_file, after_file = (prepared / ("source_integrity." + phase + ".json") for phase in ("before", "after"))
        if not before_file.is_file() or not after_file.is_file():
            raise ValueError("Metadados preparados exigem snapshots de origem antes e depois")
        before_data, after_data = (json.loads(path.read_text(encoding="utf-8-sig")) for path in (before_file, after_file))
        before_data = before_data.get("snapshot_data", before_data)
        after_data = after_data.get("snapshot_data", after_data)
        before_hashes = {"annotations.csv": before_data["annotations_sha256"].lower(), "error.csv": before_data["error_sha256"].lower()}
        after_hashes = {"annotations.csv": after_data["annotations_sha256"].lower(), "error.csv": after_data["error_sha256"].lower()}
        before_videos = canonical_inventory([row for row in before_data["inventory"] if row["relative_path"].startswith("videos/")])
        after_videos = canonical_inventory([row for row in after_data["inventory"] if row["relative_path"].startswith("videos/")])
        if before_hashes != after_hashes or after_hashes != source_before or before_videos != after_videos:
            raise RuntimeError("Fontes preparadas não preservadas; publicação recusada")
        for path in (before_file, after_file):
            shutil.copy2(path, staging / path.name)
        for name in ("execution_environment.json", "execution_manifest.json", "docker-cli.log", "source_integrity.json"):
            path = prepared / name
            if path.is_file():
                shutil.copy2(path, staging / name)
        payload = json.loads((staging / "metadata_validation.json").read_text(encoding="utf-8"))
        if payload.get("run", {}).get("dataset") != "v-librasil-raw":
            raise ValueError("Metadados preparados são de outro dataset")
    else:
        payload = validate_dataset(dataset_root / "annotations.csv", dataset_root / "videos", staging,
                                   dataset="v-librasil-raw", exceptions_csv=None,
                                   ffprobe_executable=ffprobe_executable, fps_tolerance=fps_tolerance)
    payload = rederive_comparisons(payload, dataset_root)
    inventory_after = video_inventory(dataset_root)
    source_after_probe = {name: digest(dataset_root / name) for name in source_before}
    if source_before != source_after_probe or inventory_before != inventory_after:
        raise RuntimeError("Fontes mudaram durante a inspeção; publicação recusada")
    payload["source_integrity"] = {
        "before": source_before, "after": source_after_probe,
        "video_inventory_before": inventory_digest(before_videos if prepared_metadata is not None else inventory_before),
        "video_inventory_after": inventory_digest(after_videos if prepared_metadata is not None else inventory_after),
        "video_count_before": len(before_videos if prepared_metadata is not None else inventory_before),
        "video_count_after": len(after_videos if prepared_metadata is not None else inventory_after),
        "physical_inventory_unchanged_during_publication": inventory_before == inventory_after,
        "evidence": ["source_integrity.before.json", "source_integrity.after.json"] if prepared_metadata is not None else ["metadata_validation.json"]
    }
    result = generate_vlibrasil_artifacts(dataset_root=dataset_root, metadata_payload=payload,
                                         output_root=staging, metadata_json=staging/"metadata_validation.json")
    summary = result["summary"]
    flattened = [_flatten_result(item) for item in payload["results"]]
    with (staging / "video_metadata.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(flattened[0]) if flattened else ["relative_path"])
        writer.writeheader(); writer.writerows(flattened)
    with (staging / "metadata_comparison.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(flattened[0]) if flattened else ["relative_path"])
        writer.writeheader(); writer.writerows(flattened)
    shutil.copy2(staging / "validation.log", staging / "probe_execution.log")
    (staging / "validation.log").write_text("".join(f"{item['input']['relative_path']}\t{item['probe'].get('status')}\t{item['comparison']['overall_status']}\n" for item in payload["results"]), encoding="utf-8")
    # JSON is the technical source of truth; add the quantified interpretation
    # without rewriting declared values or observed raw probe evidence.
    payload["normalization_contract"] = {"version": "v-librasil-stage1.nfc-pua.v1", "unicode": "NFC",
                                         "trim": "external", "comparison": "casefold",
                                         "private_use": {"U+F022": '"', "U+F03F": "?", "U+F05C": "\\"},
                                         "backslash": "literal filename character"}
    by_key = {}
    for row in result["manifest_rows"]:
        by_key.setdefault(normalize_filename_key(row["video_name"]), []).append(row)
    flags = ("metadata_match", "technical_valid", "dataset_valid")
    for item in payload["results"]:
        name = (item.get("csv") or {}).get("video_name") or item["input"]["relative_path"].rsplit("/", 1)[-1]
        rows = by_key.get(normalize_filename_key(name), [])
        item["validation"] = {key: rows[0][key] for key in flags} if len(rows) == 1 else {"metadata_match": "duplicate" if rows else "missing", "technical_valid": False, "dataset_valid": False}
    for csv_name in ("metadata_comparison.csv", "video_metadata.csv"):
        comparison_path = staging / csv_name
        with comparison_path.open(encoding="utf-8-sig", newline="") as stream:
            reader = csv.DictReader(stream)
            fields, comparison_rows = list(reader.fieldnames or []), list(reader)
        for field in (*flags, "normalized_key"):
            if field not in fields:
                fields.append(field)
        for row in comparison_rows:
            key = normalize_filename_key(row.get("video_name") or row.get("relative_path", "").rsplit("/", 1)[-1])
            candidates = by_key.get(key, [])
            row["normalized_key"] = key
            row.update({flag: candidates[0][flag] for flag in flags} if len(candidates) == 1 else
                       dict(metadata_match="duplicate" if candidates else "missing", technical_valid=False, dataset_valid=False))
        with comparison_path.open("w", encoding="utf-8", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=fields); writer.writeheader(); writer.writerows(comparison_rows)
    payload["stage1_fps_analysis"] = summary["fps_analysis"]
    payload["generation_id"] = generation
    payload["run"]["output_root"] = "data/processed/metadata-validation/v-librasil-raw"
    payload["run"]["input_csv"] = "data/raw/v-librasil-raw/annotations.csv"
    payload["run"]["input_root"] = "data/raw/v-librasil-raw/videos"
    payload["run"]["exceptions_csv"] = None
    payload["run"]["path_base"] = "app/"
    payload["run"]["command_paths_note"] = "probe.command preserves the actually executed container argv for audit; source/artifact references are relative to app"
    write_json(staging / "metadata_validation.json", payload)
    review = summary["stage1_review"]
    # Materialize quantified hypotheses alongside the original hypothesis rows.
    analysis = summary["fps_analysis"]
    with (staging/"fps_hypotheses_summary.csv").open("w",encoding="utf-8",newline="") as stream:
        fields = ["hypothesis","count","total_annotations","evaluable_both_hypotheses","csv_fps_matches_actual_fps","csv_fps_matches_actual_frame_count","matches_both","matches_neither","inconclusive","invalid_declared_values","coverage","hypothesis_winner","confidence","tolerance"]
        writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        counts = payload["summary"]["fps_hypothesis_counts"]
        for hypothesis in ("rate","frame_count","ambiguous","none","inconclusive","invalid"):
            writer.writerow({**analysis, "hypothesis": hypothesis, "count": counts.get(hypothesis, 0)})
    source_after = {name: digest(dataset_root / name) for name in source_before}
    if source_before != source_after:
        raise RuntimeError("Entradas tabulares mudaram durante a geração; nada foi publicado")
    stored = pd.read_parquet(staging/"manifests/v_librasil_validated.parquet")
    with (dataset_root/"annotations.csv").open(encoding="utf-8-sig",newline="") as stream:
        expected_keys = Counter(normalize_filename_key(row.get("video_name")) for row in csv.DictReader(stream))
    expected_rows = sum(expected_keys.values())
    stored_keys = Counter(normalize_filename_key(value) for value in stored["video_name"])
    if expected_keys != stored_keys or any(count != 1 for count in stored_keys.values()):
        raise RuntimeError("Identidade/chaves do manifest incoerentes ou ambíguas; nada foi publicado")
    if len(stored) != expected_rows or len(result["manifest_rows"]) != expected_rows:
        raise RuntimeError("Manifest e annotations.csv possuem contagens incoerentes")
    if any(stored["source_csv"] != "annotations.csv"):
        raise RuntimeError("Exceção entrou no manifest")
    if len(payload["results"]) != summary["counts"]["physical_videos"] + summary["key_reconciliation"]["missing"]:
        raise RuntimeError("Cobertura técnica incoerente")
    summary["generation_id"] = generation
    summary["source_hashes"] = source_after
    write_json(staging/"reports/metadata_summary.json", summary)
    source_dir = Path(__file__).parent
    code_hashes = {name: digest(source_dir / name) for name in ("metadata_validation.py", "video_metadata.py", "vlibrasil_validation.py", "stage1_review.py", "vlibrasil_publication.py")}
    write_json(staging / "derivation_provenance.json", dict(
        comparison_derivation=("Observações técnicas preservadas da execução preparada; comparações rederivadas pelo código final contra annotations.csv original" if prepared_metadata is not None else "Observações técnicas desta execução; comparações rederivadas pelo mesmo código final contra annotations.csv original"),
        source_code_sha256=code_hashes, probe_primitive_unchanged_from_repository="video_metadata.py",
        probe_commands_and_versions="metadata_validation.json: results[].probe.command and run.toolchain",
        runtime_source_snapshot_note=("Probe orchestration began before final closeout refactoring; final comparisons were rederived without changing observations" if prepared_metadata is not None else "Probe and comparisons used this generation's source code")))
    files = {p.relative_to(staging).as_posix(): digest(p) for p in sorted(staging.rglob("*")) if p.is_file()}
    write_json(staging/"publication.json", dict(generation_id=generation,dataset="v-librasil-raw",state="complete",
               artifacts_sha256=files,source_before=source_before,source_after=source_after,
               expected_manifest_rows=expected_rows,manifest_rows=len(stored),
               publication_guarantee="Complete staging, validated artifact hashes, directory rename with rollback; brief absence possible on Windows, never mixed files; registry replaced last",
               human_review="pending",global_stage1_decision=None))
    canonical=publish_generation(staging,base_root,summary,generation_id=generation) if publish else base_root/"v-librasil-raw"
    return {"canonical":canonical,"staging":staging,"generation_id":generation,"summary":summary,"published":publish}
