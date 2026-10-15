# Data Model: Validar Metadados Técnicos de Vídeo

## CSV Video Record

- **Source**: `annotations.csv` or `error.csv` under a dataset raw directory.
- **Fields**: source file, row number, `video_name`, `class`, `user_id`,
  `width`, `height`, `fps` and any available identifier.
- **Rules**: original values remain strings in the raw source; numeric parsing
  for comparison may yield a null value and must be reported.

## Observed Video Metadata

- **Source**: physical video file under `<dataset>/videos/`.
- **Fields**: `video_name`, relative path, optional SHA-256 and size,
  `actual_width`, `actual_height`, `actual_fps`, raw average and nominal rates,
  `actual_frame_count`, duration, codec, frame-count source, stream count,
  probe status, error and command metadata.
- **Rules**: null means unavailable or not determined; it is not converted to
  zero. The raw rate strings remain available for audit.

## Metadata Comparison

- **Relationship**: zero or one CSV record is matched to one physical video by
  `video_name`; a missing side remains represented in the result.
- **Fields**: expected CSV values, observed values, `width_status`,
  `height_status`, `fps_as_rate_status`, `fps_as_frame_count_status`,
  `fps_interpretation`, `overall_status`, source and error.
- **Statuses**: `ok`, `divergente`, `não comparado`, `inconclusivo`, `ausente`,
  `erro` and `atenção` as appropriate to the comparison.

## FPS Hypothesis Summary

- **Source**: aggregate of comparison rows.
- **Fields**: dataset, hypothesis, status, quantity and explanatory note.
- **Hypotheses**: `csv_fps_is_actual_fps`, `csv_fps_is_frame_count`,
  `csv_fps_matches_neither`, `inconclusive`, `ambiguous` and `mixed`.

## Validation Execution

- **Fields**: schema version, dataset, raw and output directories, annotations
  and exception files, tool executable, tool versions, image identity when
  available, command parameters, FPS tolerance, start time, end time, counts
  and failures.
- **Relationship**: one execution produces one JSON source of truth plus CSV
  projections and a log for one dataset.

## Output Artifacts

```text
data/processed/metadata-validation/<dataset>/
├── metadata_validation.json
├── video_metadata.csv
├── metadata_comparison.csv
├── fps_hypotheses_summary.csv
├── toolchain.json
└── validation.log
```

All paths in this model are derived outputs. The raw video and CSV files are
never overwritten by validation.

## Provenance Issue

- **Source**: reconciliation of `annotations.csv`, `error.csv`, `videos/`, the
  filename convention result and `metadata_validation.json`.
- **Fields**: dataset, severity, code, video name, source, row number, message
  and evidence.
- **Severities**: `CRITICAL`, `ERROR`, `WARNING` and `INFO`.
- **Decision**: `GO` only when no `CRITICAL` or `ERROR` issue exists;
  otherwise `NO-GO`.
- **V-LIBRASIL rule**: `error.csv` is a required provenance source. A missing
  annotation file, an exception not present in `annotations.csv`, an
  inconsistent reason or a silent missing physical file is recorded rather
  than inferred away.

## Validated Manifest

One derived Parquet row represents each union member of the annotation,
exception, physical-video and technical-result keys. Original CSV columns are
preserved when available and may be accompanied by `actual_width`,
`actual_height`, `actual_fps`, `actual_frame_count`, `actual_duration`,
`file_exists`, `file_readable`, `filename_valid`, `metadata_valid`,
`validation_status` and `validation_notes`.
