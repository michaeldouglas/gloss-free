"""CSV-to-video metadata validation with JSON as the source of truth."""

from __future__ import annotations

import csv
import hashlib
import json
import os
import subprocess
import tempfile
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path, PurePosixPath
from typing import Any, Callable

from .video_metadata import probe_video


ProbeFunction = Callable[[Path], dict[str, Any]]
VIDEO_SUFFIXES = {".avi", ".flv", ".m4v", ".mkv", ".mov", ".mp4", ".webm", ".wmv"}
DEFAULT_FPS_TOLERANCE = 0.01
DATASET_FILESYSTEM_KEY_COLUMNS = {
    "minds-libras-raw": "video_id",
}


def filesystem_key_column(dataset: str) -> str:
    """Return the annotation column that identifies a physical video file."""

    return DATASET_FILESYSTEM_KEY_COLUMNS.get(dataset, "video_name")


def _json_default(value: Any) -> Any:
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, Path):
        return str(value)
    raise TypeError(f"valor não serializável: {type(value).__name__}")


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            "w", encoding="utf-8", dir=path.parent, delete=False, suffix=".tmp"
        ) as stream:
            temporary_path = Path(stream.name)
            json.dump(payload, stream, ensure_ascii=False, indent=2, default=_json_default)
            stream.write("\n")
        os.replace(temporary_path, path)
    finally:
        if temporary_path and temporary_path.exists():
            temporary_path.unlink()


def _write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def _parse_csv_int(value: Any) -> tuple[int | None, str]:
    if value is None or str(value).strip() == "":
        return None, "missing"
    try:
        parsed = Decimal(str(value).strip())
    except (InvalidOperation, ValueError, TypeError):
        return None, "invalid"
    if not parsed.is_finite() or parsed != parsed.to_integral_value() or parsed < 0:
        return None, "invalid"
    return int(parsed), "available"


def _parse_csv_decimal(value: Any) -> tuple[Decimal | None, str]:
    if value is None or str(value).strip() == "":
        return None, "missing"
    try:
        parsed = Decimal(str(value).strip())
    except (InvalidOperation, ValueError, TypeError):
        return None, "invalid"
    if not parsed.is_finite() or parsed < 0:
        return None, "invalid"
    return parsed, "available"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _safe_relative_path(value: str, root: Path) -> Path | None:
    normalized = value.replace("\\", "/")
    candidate = PurePosixPath(normalized)
    if candidate.is_absolute() or ".." in candidate.parts:
        return None
    path = (root / Path(*candidate.parts)).resolve()
    try:
        path.relative_to(root.resolve())
    except ValueError:
        return None
    return path


def _relative_path(path: Path, root: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def _status_for_expected_vs_actual(expected: Any, expected_status: str, actual: Any, actual_status: str) -> str:
    if expected_status == "invalid":
        return "invalid"
    if expected_status == "missing" or actual_status not in {"available", "ok"}:
        return "inconclusive"
    return "match" if expected == actual else "mismatch"


def classify_fps_hypotheses(
    csv_fps: Decimal | None,
    csv_fps_status: str,
    actual_fps: float | None,
    actual_fps_status: str,
    actual_frame_count: int | None,
    actual_frame_count_status: str,
    *,
    tolerance: Decimal = Decimal(str(DEFAULT_FPS_TOLERANCE)),
) -> dict[str, str]:
    """Classify rate and frame-count hypotheses independently."""

    if csv_fps_status == "invalid":
        rate_status = frame_status = "invalid"
    elif csv_fps_status == "missing":
        rate_status = frame_status = "inconclusive"
    else:
        rate_status = "inconclusive"
        if actual_fps_status in {"available", "ok"} and actual_fps is not None:
            rate_status = "match" if abs(csv_fps - Decimal(str(actual_fps))) <= tolerance else "mismatch"
        frame_status = "inconclusive"
        if actual_frame_count_status in {"available", "ok"} and actual_frame_count is not None:
            frame_status = "match" if csv_fps == Decimal(actual_frame_count) else "mismatch"

    if rate_status == "match" and frame_status == "match":
        hypothesis = "ambiguous"
    elif rate_status == "match":
        hypothesis = "rate"
    elif frame_status == "match":
        hypothesis = "frame_count"
    elif rate_status == "inconclusive" or frame_status == "inconclusive":
        hypothesis = "inconclusive"
    elif rate_status == "invalid" and frame_status == "invalid":
        hypothesis = "invalid"
    else:
        hypothesis = "none"
    return {
        "fps_rate_status": rate_status,
        "fps_frame_count_status": frame_status,
        "fps_hypothesis": hypothesis,
    }


def _aggregate_fps_interpretation(hypotheses: list[str]) -> str:
    definitive = {
        value
        for value in hypotheses
        if value not in {"inconclusive", "invalid", "not_in_csv"}
    }
    if not definitive:
        return "inconclusive"
    if len(definitive) > 1:
        return "mixed"
    return next(iter(definitive))


def _comparison_for_missing_csv() -> dict[str, Any]:
    return {
        "csv_width": None,
        "csv_height": None,
        "csv_fps_raw": None,
        "csv_fps_numeric": None,
        "width_status": "not_in_csv",
        "height_status": "not_in_csv",
        "fps_rate_status": "not_in_csv",
        "fps_frame_count_status": "not_in_csv",
        "fps_hypothesis": "not_in_csv",
        "overall_status": "not_in_csv",
    }


def _flatten_result(result: dict[str, Any]) -> dict[str, Any]:
    csv_record = result.get("csv") or {}
    probe = result["probe"]
    comparison = result["comparison"]
    return {
        "relative_path": result["input"].get("relative_path"),
        "video_id": csv_record.get("video_id"),
        "video_name": csv_record.get("video_name"),
        "csv_width": comparison.get("csv_width"),
        "actual_width": probe.get("actual_width"),
        "width_status": comparison.get("width_status"),
        "csv_height": comparison.get("csv_height"),
        "actual_height": probe.get("actual_height"),
        "height_status": comparison.get("height_status"),
        "csv_fps_raw": comparison.get("csv_fps_raw"),
        "csv_fps_numeric": comparison.get("csv_fps_numeric"),
        "actual_fps": probe.get("actual_fps"),
        "actual_fps_source": probe.get("actual_fps_source"),
        "actual_frame_count": probe.get("actual_frame_count"),
        "actual_frame_count_source": probe.get("actual_frame_count_source"),
        "actual_duration_seconds": probe.get("actual_duration_seconds"),
        "codec": probe.get("codec"),
        "fps_rate_status": comparison.get("fps_rate_status"),
        "fps_frame_count_status": comparison.get("fps_frame_count_status"),
        "fps_hypothesis": comparison.get("fps_hypothesis"),
        "overall_status": comparison.get("overall_status"),
        "error": probe.get("error"),
    }


def _summary(results: list[dict[str, Any]], *, dataset: str, tolerance: float) -> dict[str, Any]:
    comparisons = [result["comparison"] for result in results]
    hypotheses = [comparison["fps_hypothesis"] for comparison in comparisons]
    return {
        "dataset": dataset,
        "videos_seen": len(results),
        "videos_ok": sum(result["probe"].get("status") == "ok" for result in results),
        "videos_partial": sum(result["probe"].get("status") == "partial" for result in results),
        "videos_with_probe_error": sum(result["probe"].get("status") == "error" for result in results),
        "width_matches": sum(comparison.get("width_status") == "match" for comparison in comparisons),
        "height_matches": sum(comparison.get("height_status") == "match" for comparison in comparisons),
        "fps_rate_matches": sum(comparison.get("fps_rate_status") == "match" for comparison in comparisons),
        "fps_frame_count_matches": sum(
            comparison.get("fps_frame_count_status") == "match" for comparison in comparisons
        ),
        "fps_none_matches": sum(comparison.get("fps_hypothesis") == "none" for comparison in comparisons),
        "fps_inconclusive": sum(comparison.get("fps_hypothesis") == "inconclusive" for comparison in comparisons),
        "fps_hypothesis_counts": {
            hypothesis: hypotheses.count(hypothesis)
            for hypothesis in sorted(set(hypotheses))
        },
        "dataset_fps_interpretation": _aggregate_fps_interpretation(hypotheses),
        "fps_tolerance": tolerance,
    }


def _tool_version(executable: str, runner: Any) -> dict[str, Any]:
    command = [executable, "-version"]
    try:
        completed = runner(command, shell=False, capture_output=True, text=True, check=False)
    except (OSError, TypeError) as exc:
        return {
            "executable": executable,
            "command": command,
            "version": None,
            "exit_code": None,
            "stderr": "",
            "error": str(exc),
        }
    first_line = completed.stdout.splitlines()[0] if completed.stdout else None
    return {
        "executable": executable,
        "command": command,
        "version": first_line,
        "exit_code": completed.returncode,
        "stderr": completed.stderr,
    }


def _toolchain(ffprobe_executable: str, ffmpeg_executable: str, runner: Any) -> dict[str, Any]:
    ffprobe = _tool_version(ffprobe_executable, runner)
    ffmpeg = _tool_version(ffmpeg_executable, runner)
    return {
        "ffprobe_executable": ffprobe_executable,
        "ffprobe_version": ffprobe["version"],
        "ffprobe_exit_code": ffprobe["exit_code"],
        "ffprobe_stderr": ffprobe["stderr"],
        "ffmpeg_executable": ffmpeg_executable,
        "ffmpeg_version": ffmpeg["version"],
        "ffmpeg_exit_code": ffmpeg["exit_code"],
        "ffmpeg_stderr": ffmpeg["stderr"],
    }


def validate_dataset(
    annotations_csv: Path,
    videos_root: Path,
    output_dir: Path,
    *,
    dataset: str = "unknown",
    exceptions_csv: Path | None = None,
    ffprobe_executable: str = "ffprobe",
    ffmpeg_executable: str = "ffmpeg",
    fps_tolerance: float = DEFAULT_FPS_TOLERANCE,
    probe_function: ProbeFunction = probe_video,
    tool_runner: Any = subprocess.run,
) -> dict[str, Any]:
    """Validate CSV declarations against physical videos and write artifacts."""

    annotations_csv = Path(annotations_csv).resolve()
    videos_root = Path(videos_root).resolve()
    output_dir = Path(output_dir).resolve()
    key_column = filesystem_key_column(dataset)
    with annotations_csv.open("r", encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        fieldnames = reader.fieldnames or []
        required = {"video_name", "width", "height", "fps", key_column}
        missing = sorted(required - set(fieldnames))
        if missing:
            raise ValueError(f"CSV sem as colunas obrigatórias: {', '.join(missing)}")
        records = list(reader)

    rows_by_path: dict[Path, dict[str, str]] = {}
    for record in records:
        raw_name = (record.get(key_column) or "").strip()
        if raw_name:
            candidate = _safe_relative_path(raw_name, videos_root)
            if candidate is not None:
                rows_by_path[candidate] = {**record, "_csv_source": annotations_csv.name}

    if exceptions_csv is not None and Path(exceptions_csv).is_file():
        exceptions_path = Path(exceptions_csv).resolve()
        with exceptions_path.open("r", encoding="utf-8-sig", newline="") as stream:
            exception_reader = csv.DictReader(stream)
            exception_fields = exception_reader.fieldnames or []
            missing_exception_fields = sorted(required - set(exception_fields))
            if missing_exception_fields:
                raise ValueError(
                    f"CSV de exceções sem as colunas obrigatórias: {', '.join(missing_exception_fields)}"
                )
            for record in exception_reader:
                raw_name = (record.get(key_column) or "").strip()
                if raw_name:
                    candidate = _safe_relative_path(raw_name, videos_root)
                    if candidate is not None and candidate not in rows_by_path:
                        rows_by_path[candidate] = {**record, "_csv_source": exceptions_path.name}

    video_paths = sorted(
        path.resolve()
        for path in videos_root.rglob("*")
        if path.is_file() and path.suffix.lower() in VIDEO_SUFFIXES
    )
    ordered_paths = list(video_paths)
    for candidate in rows_by_path:
        if candidate not in ordered_paths:
            ordered_paths.append(candidate)

    results: list[dict[str, Any]] = []
    log_lines: list[str] = []
    tolerance_decimal = Decimal(str(fps_tolerance))
    for video_path in ordered_paths:
        record = rows_by_path.get(video_path)
        relative = _relative_path(video_path, videos_root)
        input_info: dict[str, Any] = {"relative_path": relative, "sha256": None, "size_bytes": None}
        if video_path.is_file():
            input_info["sha256"] = _sha256(video_path)
            input_info["size_bytes"] = video_path.stat().st_size

        if record is None:
            if video_path.is_file():
                try:
                    probe = probe_function(video_path)
                except Exception as exc:  # isolate a failure to this file
                    probe = {"status": "error", "error": {"message": str(exc)}}
            else:
                probe = {
                    "status": "error",
                    "error": {"message": "arquivo físico não pôde ser lido"},
                }
            comparison = _comparison_for_missing_csv()
        elif not video_path.is_file():
            probe = {
                "status": "error",
                "exit_code": None,
                "command": [],
                "actual_width": None,
                "actual_height": None,
                "actual_fps": None,
                "actual_fps_source": "none",
                "actual_frame_count": None,
                "actual_frame_count_source": "none",
                "actual_duration_seconds": None,
                "actual_duration_source": "none",
                "codec": None,
                "field_status": {},
                "error": {"message": "arquivo de vídeo referenciado no CSV não existe"},
            }
            comparison = {
                "csv_width": record.get("width"),
                "csv_height": record.get("height"),
                "csv_fps_raw": record.get("fps"),
                "csv_fps_numeric": None,
                "width_status": "inconclusive",
                "height_status": "inconclusive",
                "fps_rate_status": "inconclusive",
                "fps_frame_count_status": "inconclusive",
                "fps_hypothesis": "inconclusive",
                "overall_status": "error",
            }
        else:
            try:
                probe = probe_function(video_path)
            except Exception as exc:  # isolate a failure to this file
                probe = {
                    "status": "error",
                    "error": {"message": str(exc)},
                    "actual_width": None,
                    "actual_height": None,
                    "actual_fps": None,
                    "actual_frame_count": None,
                    "field_status": {},
                }
            csv_width, csv_width_status = _parse_csv_int(record.get("width"))
            csv_height, csv_height_status = _parse_csv_int(record.get("height"))
            csv_fps, csv_fps_status = _parse_csv_decimal(record.get("fps"))
            fps_comparison = classify_fps_hypotheses(
                csv_fps,
                csv_fps_status,
                probe.get("actual_fps"),
                probe.get("field_status", {}).get("fps", "missing"),
                probe.get("actual_frame_count"),
                probe.get("field_status", {}).get("frame_count", "unavailable"),
                tolerance=tolerance_decimal,
            )
            width_status = _status_for_expected_vs_actual(
                csv_width, csv_width_status, probe.get("actual_width"), probe.get("field_status", {}).get("width", "missing")
            )
            height_status = _status_for_expected_vs_actual(
                csv_height, csv_height_status, probe.get("actual_height"), probe.get("field_status", {}).get("height", "missing")
            )
            if probe.get("status") == "error":
                overall_status = "error"
            elif width_status == "mismatch" or height_status == "mismatch" or fps_comparison["fps_hypothesis"] == "none":
                overall_status = "mismatch"
            elif "inconclusive" in {width_status, height_status, fps_comparison["fps_hypothesis"]}:
                overall_status = "inconclusive"
            else:
                overall_status = "match"
            comparison = {
                "csv_width": csv_width,
                "csv_height": csv_height,
                "csv_fps_raw": record.get("fps"),
                "csv_fps_numeric": csv_fps,
                "width_status": width_status,
                "height_status": height_status,
                **fps_comparison,
                "overall_status": overall_status,
            }

        result = {"input": input_info, "csv": record, "probe": probe, "comparison": comparison}
        results.append(result)
        log_lines.append(f"{relative}\t{probe.get('status')}\t{comparison.get('overall_status')}\n")

    finished_at = datetime.now(timezone.utc).isoformat()
    payload = {
        "schema_version": "video-metadata-validation.v1",
        "run": {
            "dataset": dataset,
            "filesystem_key_column": key_column,
            "finished_at_utc": finished_at,
            "input_csv": str(annotations_csv),
            "exceptions_csv": str(exceptions_csv.resolve()) if exceptions_csv else None,
            "input_root": str(videos_root),
            "output_root": str(output_dir),
            "fps_tolerance": fps_tolerance,
            "toolchain": _toolchain(ffprobe_executable, ffmpeg_executable, tool_runner),
        },
        "results": results,
        "summary": _summary(results, dataset=dataset, tolerance=fps_tolerance),
    }
    _write_json(output_dir / "metadata_validation.json", payload)
    _write_json(output_dir / "toolchain.json", payload["run"]["toolchain"])
    _write_csv(
        output_dir / "video_metadata.csv",
        [_flatten_result(result) for result in results],
        list(_flatten_result(results[0]).keys()) if results else ["relative_path"],
    )
    _write_csv(
        output_dir / "metadata_comparison.csv",
        [result["comparison"] | {"relative_path": result["input"].get("relative_path")} for result in results],
        ["relative_path", "csv_width", "csv_height", "csv_fps_raw", "csv_fps_numeric", "width_status", "height_status", "fps_rate_status", "fps_frame_count_status", "fps_hypothesis", "overall_status"],
    )
    _write_csv(
        output_dir / "fps_hypotheses_summary.csv",
        [{"hypothesis": hypothesis, "count": count} for hypothesis, count in payload["summary"]["fps_hypothesis_counts"].items()],
        ["hypothesis", "count"],
    )
    (output_dir / "validation.log").write_text("".join(log_lines), encoding="utf-8")
    return payload
