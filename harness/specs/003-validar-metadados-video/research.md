# Research: Validar Metadados Técnicos de Vídeo

## Decision 1: Preserve multiple frame-rate signals

**Decision**: Preserve both the average frame rate and the stream/container
nominal rate. Use the average rate as `actual_fps` for the primary comparison
when it is valid; record which source was selected and keep both raw ratios.

**Rationale**: A video can expose distinct nominal and average rates, and
discarding one would hide evidence needed to interpret the CSV. A rational such
as `30000/1001` must be parsed without rounding the stored raw value.

**Alternatives considered**: Selecting only `r_frame_rate` would reflect the
stream time base rather than necessarily the observed playback rate. Selecting
only a rounded decimal would make the comparison and later audit less precise.

## Decision 2: Treat frame count as nullable and auditable

**Decision**: Read `nb_frames` first. If absent, perform a count-frames probe
and store the source as `nb_read_frames`; if both are unavailable, store a null
value and `frame_count_status=not_determined`.

**Rationale**: A missing metadata field is not equivalent to zero frames. The
fallback provides a useful observation while making its higher processing cost
visible. Estimating frames as duration multiplied by FPS is not evidence of an
actual frame count.

**Alternatives considered**: Inferring frames as `fps * duration` was rejected
because it can hide variable frame rate and rounding behavior.

## Decision 3: Keep inspection separate from notebook presentation

**Decision**: The reusable Python module and CLI produce a JSON source of truth
and tabular projections under
`data/processed/metadata-validation/<dataset>/`; the notebook invokes the CLI
through the existing Docker service and reads those files for display.

**Rationale**: The notebook remains readable and reproducible without copying
the probing logic. Docker supplies the pinned video toolchain while the raw
mount stays read-only.

**Alternatives considered**: Calling `ffprobe` directly from every notebook
cell would duplicate orchestration and make the result dependent on the host's
installed toolchain.

## Decision 4: Classify FPS hypotheses independently

**Decision**: Emit separate statuses for `csv.fps == actual_fps` and
`csv.fps == actual_frame_count`, plus a derived interpretation of `rate`,
`frame_count`, `none`, `ambiguous`, `mixed` or `inconclusive`. Use and record a
numeric tolerance of `0.01` for rate comparison.

**Rationale**: The original `fps` label is evidence under investigation, not a
contract that may be silently corrected. Independent statuses retain the
discovery result at row and aggregate levels.

**Alternatives considered**: Renaming the column to `frame_count` or assuming
that every integer is FPS would erase the uncertainty the feature is intended
to resolve.

## Decision 5: Failure isolation and stream ambiguity

**Decision**: Process each candidate video independently and append a structured
error result when a file is missing, unreadable, invalid or not probeable. Select
the first video stream for primary values, but record the number of video
streams and flag multiple streams for review.

**Rationale**: A large dataset must still provide useful evidence when a small
subset is damaged. Multiple streams can make a silent choice scientifically
misleading, so the choice must remain visible.

**Alternatives considered**: Aborting on the first error or silently merging
multiple video streams was rejected because both approaches hide uncertainty.

## Decision 6: Toolchain traceability

**Decision**: Record the exact probe commands, exit codes, stderr, versions of
FFmpeg/ffprobe and, when available, the Docker image digest. The Dockerfile and
Compose security boundary remain unchanged unless implementation validation
finds a concrete gap.

**Rationale**: The current image is digest-pinned at the base image, runs as a
non-root user, disables network access and mounts raw data read-only, but the
effective Debian FFmpeg version can change on rebuild. Recording the toolchain
prevents a successful command from being mistaken for a reproducible result.

**Alternatives considered**: Recording only the image tag or only a successful
exit code was rejected because neither identifies the effective media toolchain
or partial failures.
