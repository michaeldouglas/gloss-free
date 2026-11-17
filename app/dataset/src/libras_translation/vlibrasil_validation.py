"""V-LIBRASIL Stage 1 integrity projections; raw data is immutable."""
from __future__ import annotations
import csv
import json
import math
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit
from .metadata_validation import normalize_filename_key

SEVERITIES = ("CRITICAL", "ERROR", "WARNING", "INFO")
KNOWN_EXCEPTIONS = {"Congelar_Articulador3.mp4", "Criança_Articulador3.mp4", "Poesia_Articulador2.mp4"}

def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, default=str) + "\n", encoding="utf-8")

def read_csv(path):
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return [{**row, "_row_number": number} for number, row in enumerate(csv.DictReader(stream), 2)]

def write_csv(path, rows, fields):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)

def positive(value):
    try:
        number = float(value)
        return math.isfinite(number) and number > 0
    except (TypeError, ValueError):
        return False

def valid_url(value):
    try:
        parts = urlsplit(str(value or "").strip())
        return parts.scheme.casefold() in {"http", "https"} and bool(parts.netloc)
    except ValueError:
        return False

def technical_valid(probe):
    return bool(probe.get("status") in {"ok", "partial"} and probe.get("video_stream_count", 0) > 0
                and all(positive(probe.get(field)) for field in ("actual_width", "actual_height", "actual_fps", "actual_duration_seconds"))
                and probe.get("codec"))

def filename_valid(name, record):
    key = normalize_filename_key(name)
    if not key.endswith(".mp4") or "_" not in key[:-4]:
        return False
    class_name, user = key[:-4].rsplit("_", 1)
    return bool(re.fullmatch(r"articulador\d+", user)
                and class_name == normalize_filename_key(record.get("class"))
                and user == normalize_filename_key(record.get("user_id")))

def generate_vlibrasil_artifacts(*, dataset_root, metadata_payload, output_root, metadata_json=None):
    import pandas as pd
    dataset_root, output_root = Path(dataset_root).resolve(), Path(output_root).resolve()
    annotations, exceptions = read_csv(dataset_root / "annotations.csv"), read_csv(dataset_root / "error.csv")
    groups, physical, observed, exception_groups = (defaultdict(list) for _ in range(4))
    for row in annotations:
        groups[normalize_filename_key(row.get("video_name"))].append(row)
    for row in exceptions:
        exception_groups[normalize_filename_key(row.get("video_name"))].append(row)
    for file in sorted((dataset_root / "videos").rglob("*")):
        if file.is_file() and file.suffix.casefold() in {".mp4", ".avi", ".mkv", ".mov", ".webm", ".m4v", ".flv", ".wmv"}:
            physical[normalize_filename_key(file.name)].append(file)
    for result in metadata_payload.get("results", []):
        name = result.get("input", {}).get("relative_path", "").rsplit("/", 1)[-1]
        observed[normalize_filename_key(name)].append(result)
    issues, exception_rows, manifest = [], [], []
    def issue(severity, code, message, key="", source="", row_number=None, evidence=None):
        issues.append(dict(dataset="v-librasil-raw", severity=severity, code=code, message=message,
                           normalized_key=key, source=source, row_number=row_number,
                           evidence=json.dumps(evidence, ensure_ascii=False, default=str)))
    for key, rows in groups.items():
        if not key or len(rows) != 1:
            issue("CRITICAL", "annotation_key_collision", "Chave vazia ou não única", key, "annotations.csv",
                  evidence=[row.get("video_name") for row in rows])
    ids = defaultdict(list)
    for row in annotations:
        ids[normalize_filename_key(row.get("video_id"))].append(row)
    for identity, rows in ids.items():
        if not identity or len(rows) > 1:
            for row in rows:
                issue("CRITICAL", "annotation_id_collision", "video_id vazio ou não único",
                      normalize_filename_key(row.get("video_name")), "annotations.csv", row["_row_number"])
    for key, paths in physical.items():
        if len(paths) != 1:
            issue("CRITICAL", "physical_key_collision", "Chave física normalizada não única", key, "videos/", evidence=[p.name for p in paths])
        if key not in groups and key not in exception_groups:
            issue("ERROR", "unregistered_physical_file", "Vídeo físico sem registro", key, "videos/")
    expected = {normalize_filename_key(name) for name in KNOWN_EXCEPTIONS}
    if set(exception_groups) != expected:
        issue("ERROR", "exception_set_changed", "Exceções divergem das três documentadas", source="error.csv", evidence=sorted(exception_groups))
    for key, rows in exception_groups.items():
        if len(rows) != 1:
            issue("CRITICAL", "exception_key_collision", "Exceção normalizada não única", key, "error.csv")
    for row in exceptions:
        key = normalize_filename_key(row.get("video_name"))
        try:
            zeros = all(float(row[field]) == 0 for field in ("width", "height", "fps"))
        except (ValueError, TypeError, KeyError):
            zeros = False
        documented = key in expected and len(exception_groups[key]) == 1 and key not in groups and not physical.get(key) and zeros and filename_valid(str(row.get("video_name") or ""), row)
        exception_rows.append(dict(video_name=row.get("video_name"), normalized_key=key, in_annotations=key in groups,
                                   physical_file_exists=bool(physical.get(key)), documented_exception=documented,
                                   excluded_from_manifest=True, reason="Ausência documentada; campos técnicos zerados na origem" if documented else "Proveniência inconsistente"))
        issue("INFO" if documented else "ERROR", "documented_exception" if documented else "exception_inconsistent",
              exception_rows[-1]["reason"], key, "error.csv", row["_row_number"], exception_rows[-1])
    required = {"video_id", "video_name", "class", "user_id", "width", "height", "fps", "url_page", "url_download"}
    if not annotations:
        issue("CRITICAL", "annotations_empty", "annotations.csv vazio", source="annotations.csv")
    for row in annotations:
        key = normalize_filename_key(row.get("video_name"))
        paths, candidates = physical.get(key, []), observed.get(key, [])
        unique = bool(key and len(groups[key]) == len(paths) == len(candidates) == 1)
        item = candidates[0] if unique else {}
        probe, comparison = item.get("probe", {}), item.get("comparison", {})
        schema = required <= row.keys() and all(str(row.get(f) or "").strip() for f in required) and all(positive(row.get(f)) for f in ("width", "height", "fps")) and all(valid_url(row.get(f)) for f in ("url_page", "url_download"))
        if not schema:
            issue("ERROR", "annotation_values_invalid", "Campos obrigatórios inválidos", key, "annotations.csv", row["_row_number"])
        if len(groups[key]) > 1 or len(paths) > 1 or len(candidates) > 1:
            state = "duplicate"
        elif not paths:
            state = "missing"
            issue("ERROR", "silent_missing_file", "Anotação sem vídeo físico", key, "annotations.csv", row["_row_number"])
        elif not candidates or comparison.get("overall_status") in {"inconclusive", "error"}:
            state = "inconclusive"
        elif comparison.get("width_status") == comparison.get("height_status") == "match" and (
                comparison.get("fps_rate_status") == "match" or comparison.get("fps_frame_count_status") == "match"):
            state = "match"
        else:
            state = "mismatch"
        tech, convention = unique and technical_valid(probe), filename_valid(str(row.get("video_name") or ""), row)
        if paths and unique and not tech:
            issue("ERROR", "technical_invalid", "Metadados técnicos essenciais indisponíveis ou inválidos", key, "videos/", evidence=probe.get("error"))
        if state in {"mismatch", "inconclusive"}:
            issue("WARNING", "metadata_" + state, "Comparação declarada requer revisão", key, "metadata_validation.json", row["_row_number"], comparison)
        if not convention:
            issue("ERROR", "filename_invalid", "Nome não corresponde à classe/articulador", key, "annotations.csv", row["_row_number"])
        blocked = any(i["normalized_key"] == key and i["severity"] in {"CRITICAL", "ERROR"} for i in issues)
        valid = bool(schema and unique and tech and convention and state == "match" and not blocked)
        manifest.append({**{k: v for k, v in row.items() if not k.startswith("_")}, "dataset": "v-librasil-raw",
                         "source_csv": "annotations.csv", "annotation_row": row["_row_number"], "filesystem_key": key,
                         "filesystem_original_name": paths[0].name if len(paths) == 1 else None,
                         "relative_path": paths[0].relative_to(dataset_root / "videos").as_posix() if len(paths) == 1 else None,
                         "file_exists": bool(paths), "file_readable": bool(unique and probe.get("status") in {"ok", "partial"}),
                         "filename_valid": convention, "metadata_match": state, "metadata_valid": state == "match",
                         "technical_valid": bool(tech), "dataset_valid": valid,
                         **{f: probe.get(f) for f in ("actual_width", "actual_height", "actual_fps", "actual_frame_count", "codec")},
                         "actual_duration": probe.get("actual_duration_seconds"),
                         "validation_status": "valid" if valid else "requires_review"})
    severity = Counter(i["severity"] for i in issues)
    valid_count = sum(row["dataset_valid"] for row in manifest)
    extras = sum(len(paths) for key, paths in physical.items() if key not in groups and key not in exception_groups)
    dataset_ok = bool(annotations and valid_count == len(annotations) and not extras and not severity["ERROR"] and not severity["CRITICAL"])
    summary = dict(schema_version="dataset-validation-summary.v1", dataset="v-librasil-raw",
                   generated_at_utc=datetime.now(timezone.utc).isoformat(), decision="GO" if dataset_ok else "NO-GO",
                   decision_scope="Somente integridade V-LIBRASIL; sem decisão global Etapa 1", review_status="pending_human_review", dataset_valid=dataset_ok)
    summary["source"] = {"annotations_csv": "data/raw/v-librasil-raw/annotations.csv", "error_csv": "data/raw/v-librasil-raw/error.csv",
                         "metadata_validation": "data/processed/metadata-validation/v-librasil-raw/metadata_validation.json"}
    summary["counts"] = dict(annotations=len(annotations), exceptions=len(exceptions), physical_videos=sum(map(len, physical.values())),
                            manifest_rows=len(manifest), valid=valid_count, issues=len(issues), by_severity={s: severity[s] for s in SEVERITIES},
                            affected_files=len({i["normalized_key"] for i in issues if i["normalized_key"] in physical}),
                            affected_annotations=len({row["_row_number"] for row in annotations if any(i["normalized_key"] == normalize_filename_key(row.get("video_name")) for i in issues)}),
                            unreadable_files=sum(i.get("input", {}).get("size_bytes") is not None and i.get("probe", {}).get("status") == "error" for i in metadata_payload.get("results", [])),
                            provenance=dict(error_rows=len(exceptions), error_in_annotations=sum(r["in_annotations"] for r in exception_rows),
                                            error_with_physical_file=sum(r["physical_file_exists"] for r in exception_rows),
                                            error_missing_file=sum(not r["physical_file_exists"] for r in exception_rows),
                                            documented_exceptions=sum(r["documented_exception"] for r in exception_rows)))
    summary["key_reconciliation"] = dict(csv_records=len(annotations), matched=sum(len(rows) == 1 and len(physical.get(k, [])) == 1 for k, rows in groups.items()),
                                         missing=sum(len(rows) for k, rows in groups.items() if k not in physical), extra=extras,
                                         normalized_duplicate_annotations=sum(len(rows)-1 for rows in groups.values()),
                                         normalized_duplicate_physical=sum(len(paths)-1 for paths in physical.values()), filesystem_key_column="video_name")
    summary["validity_contract"] = dict(metadata_match="match/mismatch/inconclusive/missing/duplicate; unique join, dimensions and independent fps hypotheses",
                                        technical_valid="readable video stream, positive observed dimensions/fps/duration and codec, independent of CSV agreement",
                                        dataset_valid="valid annotation schema and name, unique join, technical_valid, metadata_match=match and no blocking issues")
    summary["artifacts"] = dict(report="reports/metadata_validation_report.md", issues="reports/metadata_issues.csv", manifest="manifests/v_librasil_validated.parquet", exceptions="reports/documented_exceptions.csv")
    summary["source_integrity"] = metadata_payload.get("source_integrity", {})
    from .stage1_review import build_stage1_review
    review = build_stage1_review(dataset_root, metadata_payload, summary, manifest)
    summary["stage1_review"], summary["fps_analysis"] = review, review["fps_analysis"]
    write_json(output_root / "reports/metadata_summary.json", summary)
    write_json(output_root / "reports/stage1_review.json", review)
    write_csv(output_root / "reports/metadata_issues.csv", issues, ["dataset","severity","code","message","normalized_key","source","row_number","evidence"])
    write_csv(output_root / "reports/documented_exceptions.csv", exception_rows, ["video_name","normalized_key","in_annotations","physical_file_exists","documented_exception","excluded_from_manifest","reason"])
    (output_root / "manifests").mkdir(parents=True, exist_ok=True)
    pd.DataFrame(manifest).to_parquet(output_root / "manifests/v_librasil_validated.parquet", index=False)
    lines = ["# V-LIBRASIL — fechamento da integridade da Etapa 1", "", "Pendente de revisão humana; sem decisão global da Etapa 1.", "",
             "## Contagens", "", *[f"- {k}: {v}" for k,v in summary["counts"].items()], "", "## Reconciliação", "",
             *[f"- {k}: {v}" for k,v in summary["key_reconciliation"].items()], "", "## Definições", "",
             *[f"- {k}: {v}" for k,v in summary["validity_contract"].items()], "", "## Campo fps", "",
             json.dumps(review["fps_analysis"], ensure_ascii=False, indent=2), "", "## Sete eixos operacionais", "",
             "Agrupamento desta execução a partir dos FR/SC e seções 3–8 do notebook; não é uma lista canônica pré-existente.", "",
             json.dumps(review["requirements"], ensure_ascii=False, indent=2), "", "## Exceções documentadas", "",
             *[f"- {r['video_name']}: {r['reason']}" for r in exception_rows], "", "## Evidências e limites", "",
             "- metadata_validation.json: observações por arquivo, hashes, comandos e versões.",
             "- reports/stage1_review.json: schema, unicidade, nomes especiais e critérios quantitativos.",
             "- reports/metadata_issues.csv: ocorrências; arquivos afetados são contados separadamente.",
             "- reports/documented_exceptions.csv: exceções excluídas do manifest.",
             "- manifests/v_librasil_validated.parquet: somente annotations.csv.",
             "- ffprobe não comprova decodificação completa, qualidade linguística ou adequação a treinamento."]
    (output_root / "reports/metadata_validation_report.md").write_text("\n".join(lines)+"\n", encoding="utf-8")
    return dict(summary=summary, issues=issues, manifest_rows=manifest)
