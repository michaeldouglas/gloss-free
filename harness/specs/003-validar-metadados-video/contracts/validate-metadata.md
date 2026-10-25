# Validation Command Contract

## Command

```text
libras video validate-metadata --dataset <dataset>
```

The command accepts optional paths for the annotations CSV, the exception CSV,
the derived output directory, the `ffprobe` executable and an FPS tolerance.
Relative dataset paths resolve below `data/raw/<dataset>/`; output defaults to
`data/processed/metadata-validation/<dataset>/`.

The CSV-to-filesystem join uses the dataset's declared physical key:

- V-LIBRASIL: `annotations.video_name` ↔ physical filename;
- MINDS-Libras: `annotations.video_id` ↔ physical filename.

For MINDS-Libras, `video_name` remains an original descriptive field and is
validated separately from the physical-file relationship.

## Inputs

- A configured dataset name.
- `annotations.csv`, required by default.
- `error.csv`, optional by default and treated as an explicit exception source.
- A `videos/` directory that may contain valid, missing, extra or invalid files.

## Outputs

- `metadata_validation.json`: source of truth for the run, per-file results,
  comparisons, summaries and toolchain information.
- `video_metadata.csv`: one row per physical or referenced video with observed
  values and probe status, preserving `video_id` and `video_name` when
  available.
- `metadata_comparison.csv`: one row per joined or unmatched record with CSV
  values, observed values and comparison statuses.
- `fps_hypotheses_summary.csv`: aggregate evidence for the FPS hypotheses.
- `toolchain.json`: executable, versions, commands and image information when
  available.
- `validation.log`: human-readable command and per-file diagnostics.

## Exit behavior

- Exit `0` when the command can inspect the inputs and write a complete result,
  including results containing data divergences or per-file attention statuses.
- Exit nonzero when required inputs, the toolchain or the output contract
  cannot be established.

## Notebook usage

The inventory notebook invokes this contract through the existing
`docker/video-processing/compose.yaml` service and then reads the generated
CSV/JSON files. It must not write under `data/raw/` or reimplement the probe.

## Quality and provenance command

```text
libras video validate-quality --dataset <dataset>
```

The command consumes the technical `metadata_validation.json` when it already
exists; otherwise it runs the technical validation first. For V-LIBRASIL,
`error.csv` is required and is reconciled against `annotations.csv` and the
physical `videos/` directory. The checks explicitly distinguish known
exceptions from annotation records whose files are silently absent.

The command writes the following derived artifacts below
`data/processed/metadata-validation/`:

- `reports/metadata_validation_report.md`: human-readable decision and
  evidence summary;
- `reports/metadata_issues.csv`: one row per classified issue with severity,
  code, source and evidence;
- `reports/metadata_summary.json`: machine-readable counts, source paths and
  `GO`/`NO-GO` decision, including key reconciliation and MINDS-Libras
  descriptive-name analysis;
- `manifests/v_librasil_validated.parquet` or
  `manifests/minds_libras_validated.parquet`: derived rows with original
  values plus observed metadata and validation flags.

Severity levels are `CRITICAL`, `ERROR`, `WARNING` and `INFO`. The decision is
`NO-GO` when at least one `CRITICAL` or `ERROR` exists. The command still
writes all artifacts and returns exit code `2` for that decision. Raw files are
never modified.
