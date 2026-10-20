"""Shell-free ffprobe inspection for video metadata.

The functions in this module deliberately keep the raw ffprobe values next to
their normalized values.  This makes missing values, zero and failed probes
auditable without changing the source video.
"""

from __future__ import annotations

import json
import math
import subprocess
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Callable, Sequence


ProbeRunner = Callable[..., subprocess.CompletedProcess[str]]

_MISSING = {None, "", "N/A", "NA", "null"}


def _is_missing(value: Any) -> bool:
    return value is None or (isinstance(value, str) and value.strip() in _MISSING)


def parse_rate(value: Any) -> Decimal | None:
    """Parse an ffprobe rate such as ``30000/1001`` without float rounding."""

    if _is_missing(value):
        return None
    try:
        if isinstance(value, str) and "/" in value:
            numerator_text, denominator_text = value.split("/", 1)
            numerator = Decimal(numerator_text.strip())
            denominator = Decimal(denominator_text.strip())
            if denominator == 0:
                return None
            result = numerator / denominator
        else:
            result = Decimal(str(value).strip())
    except (InvalidOperation, ValueError, TypeError, ZeroDivisionError):
        return None
    return result if result.is_finite() and result >= 0 else None


def _parse_int(value: Any) -> tuple[int | None, str]:
    if _is_missing(value):
        return None, "missing"
    try:
        decimal_value = Decimal(str(value).strip())
    except (InvalidOperation, ValueError, TypeError):
        return None, "invalid"
    if not decimal_value.is_finite() or decimal_value != decimal_value.to_integral_value():
        return None, "invalid"
    integer_value = int(decimal_value)
    return (integer_value, "available") if integer_value >= 0 else (None, "invalid")


def _parse_float(value: Any) -> tuple[float | None, str]:
    if _is_missing(value):
        return None, "missing"
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None, "invalid"
    return (parsed, "available") if math.isfinite(parsed) and parsed >= 0 else (None, "invalid")


def build_probe_command(
    video_path: Path,
    *,
    ffprobe_executable: str = "ffprobe",
    count_frames: bool = False,
) -> list[str]:
    """Build an argv list; callers must pass it to subprocess with shell=False."""

    command = [
        ffprobe_executable,
        "-v",
        "error",
        "-hide_banner",
    ]
    if count_frames:
        command.extend(["-count_frames", "-select_streams", "v:0"])
    command.extend(
        [
            "-show_entries",
            "stream=index,codec_type,codec_name,codec_long_name,width,height,avg_frame_rate,r_frame_rate,time_base,nb_frames,nb_read_frames,duration",
            "-show_entries",
            "format=filename,format_name,format_long_name,duration,size",
            "-of",
            "json=compact=0",
            str(video_path),
        ]
    )
    return command


def _first_video_stream(payload: dict[str, Any]) -> tuple[dict[str, Any] | None, list[dict[str, Any]]]:
    streams = payload.get("streams")
    if not isinstance(streams, list):
        return None, []
    video_streams = [stream for stream in streams if isinstance(stream, dict) and stream.get("codec_type") == "video"]
    return (video_streams[0] if video_streams else None), video_streams


def _load_probe_json(stdout: str) -> dict[str, Any]:
    payload = json.loads(stdout)
    if not isinstance(payload, dict):
        raise ValueError("ffprobe retornou JSON que não é um objeto")
    return payload


def _error_payload(message: str, *, command: Sequence[str], exit_code: int | None, stderr: str = "") -> dict[str, Any]:
    return {
        "status": "error",
        "exit_code": exit_code,
        "command": list(command),
        "video_stream_count": 0,
        "multiple_video_streams": False,
        "actual_width": None,
        "actual_height": None,
        "actual_fps": None,
        "actual_fps_source": "none",
        "avg_frame_rate": None,
        "r_frame_rate": None,
        "actual_frame_count": None,
        "actual_frame_count_source": "none",
        "actual_duration_seconds": None,
        "actual_duration_source": "none",
        "codec": None,
        "codec_long_name": None,
        "time_base": None,
        "format_name": None,
        "field_status": {
            "width": "error",
            "height": "error",
            "fps": "error",
            "frame_count": "error",
            "duration": "error",
            "codec": "error",
        },
        "raw": {},
        "error": {"message": message, "stderr": stderr},
    }


def normalize_probe_payload(
    payload: dict[str, Any],
    *,
    command: Sequence[str] | None = None,
    exit_code: int = 0,
    fallback_payload: dict[str, Any] | None = None,
    fallback_command: Sequence[str] | None = None,
    fallback_exit_code: int | None = None,
    fallback_stderr: str = "",
) -> dict[str, Any]:
    """Normalize primary and optional counted ffprobe JSON responses."""

    stream, video_streams = _first_video_stream(payload)
    fallback_stream, _ = _first_video_stream(fallback_payload or {})
    if stream is None:
        return _error_payload(
            "nenhuma stream de vídeo foi encontrada",
            command=command or [],
            exit_code=exit_code,
        )

    fallback_stream = fallback_stream or {}
    format_payload = payload.get("format") if isinstance(payload.get("format"), dict) else {}
    width, width_status = _parse_int(stream.get("width"))
    height, height_status = _parse_int(stream.get("height"))

    avg_rate_raw = stream.get("avg_frame_rate")
    nominal_rate_raw = stream.get("r_frame_rate")
    avg_rate = parse_rate(avg_rate_raw)
    nominal_rate = parse_rate(nominal_rate_raw)
    if avg_rate is not None:
        actual_fps = float(avg_rate)
        fps_source = "avg_frame_rate"
        fps_status = "available"
    elif nominal_rate is not None:
        actual_fps = float(nominal_rate)
        fps_source = "r_frame_rate"
        fps_status = "available"
    elif not _is_missing(avg_rate_raw) or not _is_missing(nominal_rate_raw):
        actual_fps = None
        fps_source = "none"
        fps_status = "invalid"
    else:
        actual_fps = None
        fps_source = "none"
        fps_status = "missing"

    primary_frame_count, primary_frame_status = _parse_int(stream.get("nb_frames"))
    fallback_frame_count, fallback_frame_status = _parse_int(fallback_stream.get("nb_read_frames"))
    if primary_frame_status == "available":
        frame_count = primary_frame_count
        frame_count_source = "nb_frames"
        frame_count_status = "available"
    elif fallback_frame_status == "available":
        frame_count = fallback_frame_count
        frame_count_source = "nb_read_frames"
        frame_count_status = "available"
    elif primary_frame_status == "invalid" or fallback_frame_status == "invalid":
        frame_count = None
        frame_count_source = "none"
        frame_count_status = "unavailable"
    else:
        frame_count = None
        frame_count_source = "none"
        frame_count_status = "unavailable"

    duration_raw = format_payload.get("duration")
    duration, duration_status = _parse_float(duration_raw)
    duration_source = "format.duration"
    if duration is None:
        duration, stream_duration_status = _parse_float(stream.get("duration"))
        if duration is not None:
            duration_source = "stream.duration"
            duration_status = stream_duration_status
        elif stream_duration_status == "invalid":
            duration_status = "invalid"

    fallback_error = None
    if fallback_payload is not None and (
        fallback_exit_code not in (None, 0)
        or (fallback_payload == {} and fallback_stderr)
    ):
        fallback_error = {
            "message": "a contagem complementar de frames falhou",
            "stderr": fallback_stderr,
            "exit_code": fallback_exit_code,
            "command": list(fallback_command or []),
        }

    status = "partial" if fallback_error else "ok"
    return {
        "status": status,
        "exit_code": exit_code,
        "command": list(command or []),
        "video_stream_count": len(video_streams),
        "multiple_video_streams": len(video_streams) > 1,
        "stream_index": stream.get("index"),
        "actual_width": width,
        "actual_height": height,
        "actual_fps": actual_fps,
        "actual_fps_source": fps_source,
        "avg_frame_rate": avg_rate_raw,
        "r_frame_rate": nominal_rate_raw,
        "actual_frame_count": frame_count,
        "actual_frame_count_source": frame_count_source,
        "actual_duration_seconds": duration,
        "actual_duration_source": duration_source if duration is not None else "none",
        "codec": stream.get("codec_name"),
        "codec_long_name": stream.get("codec_long_name"),
        "time_base": stream.get("time_base"),
        "format_name": format_payload.get("format_name"),
        "field_status": {
            "width": width_status,
            "height": height_status,
            "fps": fps_status,
            "frame_count": frame_count_status,
            "duration": duration_status if duration is not None else duration_status,
            "codec": "available" if not _is_missing(stream.get("codec_name")) else "missing",
        },
        "raw": {
            "nb_frames": stream.get("nb_frames"),
            "nb_read_frames": fallback_stream.get("nb_read_frames"),
            "duration": duration_raw if duration_raw is not None else stream.get("duration"),
        },
        "error": fallback_error,
    }


def probe_video(
    video_path: Path,
    *,
    ffprobe_executable: str = "ffprobe",
    runner: ProbeRunner = subprocess.run,
) -> dict[str, Any]:
    """Probe one video and optionally count frames, isolating file failures."""

    path = Path(video_path)
    command = build_probe_command(path, ffprobe_executable=ffprobe_executable)
    if not path.is_file():
        return _error_payload("arquivo de vídeo inexistente", command=command, exit_code=None)

    try:
        primary = runner(command, shell=False, capture_output=True, text=True, check=False)
    except OSError as exc:
        return _error_payload(str(exc), command=command, exit_code=None)
    if primary.returncode != 0:
        return _error_payload(
            "ffprobe falhou ao inspecionar o vídeo",
            command=command,
            exit_code=primary.returncode,
            stderr=primary.stderr,
        )
    try:
        payload = _load_probe_json(primary.stdout)
    except (json.JSONDecodeError, ValueError) as exc:
        return _error_payload(
            f"JSON inválido retornado por ffprobe: {exc}",
            command=command,
            exit_code=primary.returncode,
            stderr=primary.stderr,
        )

    stream, _ = _first_video_stream(payload)
    frame_count, frame_status = _parse_int(stream.get("nb_frames") if stream else None)
    if frame_status == "available":
        return normalize_probe_payload(
            payload,
            command=command,
            exit_code=primary.returncode,
        )

    fallback_command = build_probe_command(
        path,
        ffprobe_executable=ffprobe_executable,
        count_frames=True,
    )
    try:
        fallback = runner(
            fallback_command,
            shell=False,
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError as exc:
        return normalize_probe_payload(
            payload,
            command=command,
            exit_code=primary.returncode,
            fallback_payload={},
            fallback_command=fallback_command,
            fallback_exit_code=None,
            fallback_stderr=str(exc),
        )
    if fallback.returncode != 0:
        return normalize_probe_payload(
            payload,
            command=command,
            exit_code=primary.returncode,
            fallback_payload={},
            fallback_command=fallback_command,
            fallback_exit_code=fallback.returncode,
            fallback_stderr=fallback.stderr,
        )
    try:
        fallback_payload = _load_probe_json(fallback.stdout)
    except (json.JSONDecodeError, ValueError) as exc:
        return normalize_probe_payload(
            payload,
            command=command,
            exit_code=primary.returncode,
            fallback_payload={},
            fallback_command=fallback_command,
            fallback_exit_code=0,
            fallback_stderr=f"JSON inválido na contagem complementar: {exc}",
        )
    return normalize_probe_payload(
        payload,
        command=command,
        exit_code=primary.returncode,
        fallback_payload=fallback_payload,
        fallback_command=fallback_command,
        fallback_exit_code=fallback.returncode,
        fallback_stderr=fallback.stderr,
    )
