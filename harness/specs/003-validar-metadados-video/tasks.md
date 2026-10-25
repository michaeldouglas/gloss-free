# Tasks: Validar Metadados Técnicos de Vídeo

**Input**: Design documents from `/specs/003-validar-metadados-video/`

**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`,
`contracts/validate-metadata.md` and `quickstart.md`.

**Tests**: Included because the feature specification requires deterministic
tests and the project constitution requires automated coverage for behavioral
changes.

**Organization**: Tasks are grouped by user story and ordered by dependency.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Establish the derived-output path and the feature contracts.

- [x] T001 [P] Add the processed-data directory property and output-root helper in `../app/dataset/src/libras_translation/config.py`.
- [x] T002 [P] Add the versioned validation output schema and artifact names to `specs/003-validar-metadados-video/contracts/validate-metadata.md`.

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Create deterministic test fixtures and shared comparison rules
before implementing the user stories.

- [x] T003 [P] Create controlled ffprobe JSON fixtures for valid rates, missing frame counts, zero frame count, invalid ratios and multiple video streams in `../app/dataset/tests/fixtures/ffprobe/`.
- [x] T004 [P] Add unit tests for rational FPS parsing, nullable numeric fields, duration fallback and frame-count fallback in `../app/dataset/tests/test_video_metadata.py`.
- [x] T005 [P] Add unit tests for width/height comparisons, independent FPS hypotheses, missing files and per-file failure isolation in `../app/dataset/tests/test_metadata_validation.py`.

**Checkpoint**: Fixtures and expected behaviors are defined before the video
inspection and comparison implementations.

## Phase 3: User Story 1 - Conferir os metadados reais dos vídeos (Priority: P1) 🎯 MVP

**Goal**: Produce one auditable result per physical or referenced video with
the observed technical metadata and CSV comparisons.

**Independent Test**: Run the metadata validation against a temporary fixture
dataset and verify the JSON source of truth, detail CSV and aggregate summaries
without using `data/raw/`.

### Implementation for User Story 1

- [x] T006 [US1] Implement shell-free ffprobe invocation, JSON parsing, FPS source selection, frame-count fallback and field-level statuses in `../app/dataset/src/libras_translation/video_metadata.py`.
- [x] T007 [US1] Implement CSV loading, physical-video discovery, record matching, width/height comparison and independent FPS hypothesis classification in `../app/dataset/src/libras_translation/metadata_validation.py`.
- [x] T008 [US1] Implement JSON source-of-truth output, CSV projections, toolchain record, per-file log and failure-isolated batch execution in `../app/dataset/src/libras_translation/metadata_validation.py`.
- [x] T009 [US1] Add the `libras video validate-metadata` command, dataset/path options, output defaults and actionable exit behavior in `../app/dataset/src/libras_translation/cli.py`.
- [x] T010 [US1] Add CLI-level tests for output paths, required inputs, data divergences returning success and tool/input failures returning nonzero in `../app/dataset/tests/test_cli.py`.

**Checkpoint**: The command produces complete derived results for a fixture
dataset and never modifies its input CSV or video files.

## Phase 4: User Story 2 - Descobrir o significado da coluna `fps` (Priority: P1)

**Goal**: Make the FPS interpretation evidence explicit at row and dataset
levels without renaming the source column.

**Independent Test**: Use fixtures where the CSV value matches the real rate,
the real frame count, both, neither and neither because a field is unavailable.

- [x] T011 [US2] Add aggregate FPS hypothesis counts, `rate`, `frame_count`, `none`, `ambiguous`, `mixed` and `inconclusive` interpretations to `../app/dataset/src/libras_translation/metadata_validation.py`.
- [x] T012 [US2] Extend `../app/dataset/tests/test_metadata_validation.py` with tolerance, ambiguity, mixed-dataset and unavailable-frame-count cases.
- [x] T013 [US2] Document the FPS hypotheses, tolerance and interpretation statuses in `../app/README.md` and `specs/003-validar-metadados-video/quickstart.md`.

**Checkpoint**: The output proves what the CSV value matches, while preserving
the original `fps` name and raw value.

## Phase 5: User Story 3 - Visualizar a validação no inventário do dataset (Priority: P2)

**Goal**: Show the reusable validation results in the existing notebook before
the filename-convention section.

**Independent Test**: Execute the relevant notebook cells with generated
fixture outputs and confirm that detail and summary tables render in order.

- [x] T014 [US3] Add a notebook helper that invokes the existing Docker Compose service with an argument list and reads derived CSV/JSON results in `../app/notebooks/dataset/01_preparacao_inventario_validacao_datasets.ipynb`.
- [x] T015 [US3] Insert the `Validação dos metadados técnicos CSV × vídeo real` markdown and result tables immediately before `Validação da convenção do nome do arquivo` in `../app/notebooks/dataset/01_preparacao_inventario_validacao_datasets.ipynb`.
- [x] T016 [US3] Add notebook validation instructions, failure visibility and raw-data preservation notes to `../app/docker/video-processing/README.md` and `../app/README.md`.

**Checkpoint**: The notebook calls the reusable command, displays the result
and keeps filename validation as the next distinct analysis.

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Validate the complete feature and preserve project traceability.

- [x] T017 [P] Run the deterministic application suite with `uv run python -m unittest discover -s dataset/tests -v` from `../app/` and resolve any failures.
- [x] T018 [P] Validate the Docker Compose model and run the container toolchain smoke checks from `../app/docker/video-processing/compose.yaml`.
- [x] T019 Run the feature quickstart against a controlled fixture or documented local dataset and record limitations in `specs/003-validar-metadados-video/quickstart.md`.
- [x] T020 Run `graphify update .` from the harness root and confirm the canonical output remains under `harness/graphify-out/`.

## Phase 7: Provenance, Decision and Validated Manifests

**Purpose**: Reconcile V-LIBRASIL exceptions after filename validation and
produce explicit evidence and derived manifests for both configured datasets.

- [x] T021 Add `dataset_quality_validation.py` with error.csv provenance checks,
  silent-missing detection, four severity levels, GO/NO-GO decision and
  validated manifest row construction in `../app/dataset/src/libras_translation/`.
- [x] T022 Add the `libras video validate-quality` command, Parquet dependency,
  CLI tests and deterministic fixture tests in `../app/`.
- [x] T023 Generate `reports/metadata_validation_report.md`,
  `reports/metadata_issues.csv`, `reports/metadata_summary.json` and the two
  dataset-specific validated Parquet manifests without modifying
  `../app/data/raw/`.
- [x] T024 Insert the provenance/decision section after the filename
  convention in `../app/notebooks/dataset/01_preparacao_inventario_validacao_datasets.ipynb` and
  update the contract, quickstart and README documentation.

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: no implementation dependency.
- **Foundational (Phase 2)**: depends on Setup and blocks user stories.
- **User Story 1 (Phase 3)**: depends on foundational fixtures/tests.
- **User Story 2 (Phase 4)**: depends on the comparison output from US1.
- **User Story 3 (Phase 5)**: depends on the stable CLI/output contract from US1 and US2.
- **Polish (Phase 6)**: depends on all selected user stories.
- **Provenance and manifests (Phase 7)**: depends on the technical metadata
  output and the notebook filename-convention section from Phases 3–5.

### Parallel Opportunities

- T001 and T002 can run in parallel.
- T003, T004 and T005 can run in parallel because they have disjoint files.
- T017 and T018 can run in parallel after implementation.

### Implementation Strategy

1. Complete the shared output contract and deterministic fixtures.
2. Deliver US1 as the MVP: extraction, comparison, CLI and tests.
3. Complete US2 to make the FPS discovery auditable.
4. Complete US3 to expose the results in the inventory notebook.
5. Run the application, Docker and Graphify quality gates.
