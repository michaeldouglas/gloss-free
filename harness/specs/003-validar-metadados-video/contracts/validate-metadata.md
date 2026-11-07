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

## V-LIBRASIL Stage 1 closeout contract

This closeout is restricted to V-LIBRASIL metadata integrity and provenance.
It does not approve Stage 1 globally or establish linguistic suitability,
translation quality, exploratory findings or model performance. MINDS-Libras
inputs, artifacts and its run-registry entry must remain unchanged.

### Filename identity and exceptions

Enumerate physical files using the literal filename returned by the filesystem.
Never reinterpret an annotation filename as a path before comparing it. Apply
the same comparison-key function to annotations, enumerated filenames and
exceptions: Unicode NFC; translate U+F022 to `"`, U+F03F to `?`, U+F05C to a
literal backslash; strip external whitespace; then `casefold()`. A backslash
remains a filename character and must never be converted to `/`. Retain both
the original string and the derived comparison key.

Detect duplicate keys on each side and collisions introduced by normalization.
Do not select one candidate silently when a key has multiple candidates. Test
the `Frente\Á Frente_Articulador*`, `Cérebro (de "ervilha")_Articulador*` and
`O quê?_Articulador*` families explicitly.

The three documented `error.csv` entries (`Congelar_Articulador3.mp4`,
`Criança_Articulador3.mp4`, `Poesia_Articulador2.mp4`) are reconciled separately.
Their documented absence is not a missing annotation record or an unreadable
physical video. They must not contribute rows to the validated annotation
manifest. Unexpected overlap, additional exceptions or inconsistent provenance
must still be reported rather than excused automatically.

### Separate validity concepts

- `metadata_match`: a comparison state, distinguishing `match`, `mismatch`,
  `inconclusive`, `missing` and `duplicate`. A match requires a unique physical
  correspondence, matching declared width/height and support for at least one
  independently evaluated FPS hypothesis. Original declared values remain
  unchanged.
- `technical_valid`: validity of the observed physical video, independently of
  agreement with the CSV. Require a readable video stream, positive observed
  width, height, frame rate and duration, and an identified codec. Record missing
  frame count separately; it can make a hypothesis inconclusive without proving
  that the physical video is unreadable.
- `dataset_valid`: eligibility of an annotation record under the Stage 1
  integrity contract: valid required fields and filename convention, unique
  correspondence, `technical_valid`, `metadata_match == match`, and no blocking
  issue. The dataset-level summary additionally requires complete coverage, no
  ambiguous collisions or unregistered physical videos, consistent exceptions
  and no `ERROR`/`CRITICAL`. This is not an approval for training or translation.

### Quantitative FPS evidence

Evaluate `csv.fps == actual_fps` and `csv.fps == actual_frame_count`
independently. Record the absolute rate tolerance (default `0.01` frames/s),
exact count comparison, rate source, frame-count source, total annotations,
evaluable denominator, exclusive matches for each hypothesis, matches to both,
matches to neither, inconclusive cases and invalid declared values.

Confidence is a deterministic coverage rule, not statistical confidence:

- high: both hypotheses evaluable for every annotation, one hypothesis matches
  exclusively for 100%, and zero ambiguous, neither, inconclusive or invalid
  cases;
- moderate: both-hypothesis coverage is at least 95% and one hypothesis matches
  exclusively for at least 95% of all annotations, strictly exceeding the other;
- low/undetermined otherwise: report the counts without asserting a supported
  dataset-wide interpretation merely because one raw count is larger.

Persist these thresholds and the observed counts in JSON and the report.

### Counts and coherent publication

Report issue occurrences separately from distinct physical files and annotation
records affected. A documented absent exception is not a physical file affected
by a probe failure. Count unreadable physical files independently.

Generate the complete JSON/CSV/Markdown/Parquet set in a staging generation.
Verify schemas, row counts, cross-artifact identities and hashes before making
it canonical. Publish without mixing files from different generations, preserve
a recoverable superseded generation, and describe the real atomicity/rollback
guarantees on the host platform. Update only the V-LIBRASIL registry entry using
relative paths. Superseded legacy root-level V-LIBRASIL reports/manifests must
not remain active canonical results.

### Seven review axes

The sources contain 18 functional requirements and 8 success criteria, not a
previously numbered list of seven Stage 1 requirements. For this closeout the
following operational grouping consolidates the specification and notebook
sections 3–8. Each axis must have `PASS`, `PARTIAL` or `FAIL`, a justification
and artifact evidence; an unexecuted check cannot receive `PASS`.

| Axis | Evidence required | Specification mapping |
| --- | --- | --- |
| 1. Input reading and preservation | inventory, source identities, immutability checks | FR-001, FR-008; SC-008 |
| 2. Schema and required values | required columns, null/type/domain checks | FR-001, FR-003, FR-006 |
| 3. Keys and uniqueness | original/normalized duplicates and conflicting identifiers | FR-014, FR-017; SC-007; notebook section 4 |
| 4. CSV/filesystem reconciliation | unique matches, missing, extra and collision details | FR-011, FR-014; SC-001, SC-007 |
| 5. Technical metadata and FPS | per-video observations, comparisons, coverage and confidence | FR-002–FR-007, FR-011; SC-001–SC-003 |
| 6. Filename convention | class/articulator correspondence after approved normalization | FR-017; User Story 4; notebook section 7 |
| 7. Provenance and derived manifest | separate exception evidence, reports and manifest consistency | FR-014–FR-018; SC-007, SC-008 |

The output remains pending human review of V-LIBRASIL. Do not emit a global
Stage 1 decision or start Stage 2 as a side effect.
