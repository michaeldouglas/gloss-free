from __future__ import annotations

import json
import subprocess
import unittest
from pathlib import Path
from unittest.mock import Mock

from libras_translation.video_metadata import (
    build_probe_command,
    normalize_probe_payload,
    parse_rate,
    probe_video,
)


FIXTURES = Path(__file__).parent / "fixtures" / "ffprobe"


def load_fixture(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


class VideoMetadataTests(unittest.TestCase):
    def test_parse_rate_preserves_rational_meaning_and_rejects_zero_denominator(self):
        self.assertAlmostEqual(float(parse_rate("30000/1001")), 29.97002997, places=6)
        self.assertEqual(parse_rate("25/1"), parse_rate("25"))
        self.assertIsNone(parse_rate("0/0"))
        self.assertIsNone(parse_rate("invalid"))

    def test_normalize_primary_probe_uses_nb_frames_and_keeps_zero_distinct(self):
        result = normalize_probe_payload(load_fixture("valid_nb_frames.json"))
        self.assertEqual(result["actual_width"], 160)
        self.assertEqual(result["actual_height"], 120)
        self.assertEqual(result["actual_fps"], 25.0)
        self.assertEqual(result["actual_fps_source"], "avg_frame_rate")
        self.assertEqual(result["actual_frame_count"], 50)
        self.assertEqual(result["actual_frame_count_source"], "nb_frames")
        self.assertEqual(result["field_status"]["frame_count"], "available")

        zero = normalize_probe_payload(load_fixture("zero_frame_count.json"))
        self.assertEqual(zero["actual_frame_count"], 0)
        self.assertEqual(zero["raw"]["nb_frames"], "0")

    def test_normalize_uses_nb_read_frames_when_nb_frames_is_missing(self):
        result = normalize_probe_payload(
            load_fixture("missing_nb_frames_with_nb_read_frames.json"),
            fallback_payload=load_fixture("missing_nb_frames_with_nb_read_frames.json"),
        )
        self.assertEqual(result["actual_frame_count"], 60)
        self.assertEqual(result["actual_frame_count_source"], "nb_read_frames")
        self.assertAlmostEqual(result["actual_fps"], 30000 / 1001, places=6)
        self.assertEqual(result["actual_fps_source"], "avg_frame_rate")

    def test_missing_count_is_unavailable_and_invalid_rate_falls_back_or_stays_invalid(self):
        result = normalize_probe_payload(load_fixture("missing_frame_count.json"))
        self.assertIsNone(result["actual_frame_count"])
        self.assertEqual(result["actual_frame_count_source"], "none")
        self.assertEqual(result["field_status"]["frame_count"], "unavailable")

        invalid = normalize_probe_payload(load_fixture("invalid_ratios.json"))
        self.assertIsNone(invalid["actual_fps"])
        self.assertEqual(invalid["field_status"]["fps"], "invalid")
        self.assertEqual(invalid["field_status"]["width"], "invalid")

        stream_duration = load_fixture("invalid_ratios.json")
        stream_duration["streams"][0]["duration"] = "1.25"
        normalized = normalize_probe_payload(stream_duration)
        self.assertEqual(normalized["actual_duration_seconds"], 1.25)
        self.assertEqual(normalized["actual_duration_source"], "stream.duration")

    def test_multiple_video_streams_are_explicitly_signaled(self):
        result = normalize_probe_payload(load_fixture("multiple_video_streams.json"))
        self.assertEqual(result["video_stream_count"], 2)
        self.assertTrue(result["multiple_video_streams"])
        self.assertEqual(result["stream_index"], 0)

    def test_probe_uses_shell_false_and_performs_count_fallback(self):
        with self.subTest("commands"):
            command = build_probe_command(Path("sample.mp4"))
            self.assertNotIn("sh", command)
            self.assertEqual(command[0], "ffprobe")

        with self.subTest("invocation"):
            runner = Mock(
                side_effect=[
                    subprocess.CompletedProcess(
                        args=[],
                        returncode=0,
                        stdout=json.dumps(load_fixture("missing_frame_count.json")),
                        stderr="",
                    ),
                    subprocess.CompletedProcess(
                        args=[],
                        returncode=0,
                        stdout=json.dumps({
                            "streams": [{"index": 0, "codec_type": "video", "nb_read_frames": "36"}]
                        }),
                        stderr="",
                    ),
                ]
            )
            result = probe_video(Path(__file__), runner=runner)
            self.assertEqual(result["actual_frame_count"], 36)
            self.assertEqual(runner.call_args_list[0].kwargs["shell"], False)
            self.assertEqual(runner.call_args_list[1].kwargs["shell"], False)
            self.assertIn("-count_frames", runner.call_args_list[1].args[0])


if __name__ == "__main__":
    unittest.main()
