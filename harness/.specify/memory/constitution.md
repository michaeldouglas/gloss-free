<!--
Sync Impact Report
- Version change: template/unratified -> 1.0.0
- Modified principles: placeholder principles replaced with five project rules
  for reproducibility, boundaries, testing, traceability, and maintainability.
- Added sections: Project Constraints; Development Workflow and Quality Gates.
- Removed sections: none; the scaffold headings were retained and made concrete.
- Deferred items: none.
-->

# Libras Translation Data Acquisition Constitution

## Core Principles

### I. Reproducible Data Acquisition

Every acquisition operation MUST identify the dataset, repository revision, local
destination, and resulting status. The application MUST resolve and persist the
remote commit used for an operation so that a later run can be audited and
resumed. A successful command MUST distinguish downloaded, reused, and failed
files instead of hiding partial results.

This makes the research data pipeline repeatable and prevents an apparently
successful acquisition from being mistaken for a complete one.

### II. Explicit Application Boundaries

Application source code, tests, data, and runtime configuration MUST remain in
`../app/`. Spec Kit governance, specifications, plans, tasks, and coordination
artifacts MUST remain in this `harness/` directory. The legacy `../old/`
directory is out of scope. The application MUST preserve the project's pragmatic hybrid Flat
Architecture; new abstractions require a concrete responsibility they isolate.

This boundary keeps the executable research tool separate from its development
workflow and avoids architecture imposed only for naming purposes.

### III. Testable and Safe Changes

Every behavioral change MUST include or update automated tests at the smallest
useful level. Tests MUST be deterministic and MUST NOT require real dataset
downloads, credentials, or network access by default. Network and filesystem
integration behavior MUST be covered with controlled fakes, fixtures, or
explicitly isolated integration tests. A change MUST NOT be considered complete
when the test command is unavailable, undocumented, or reporting a false pass.

The test suite is a safety boundary for acquisition logic, manifest transitions,
CLI validation, retries, and error reporting.

### IV. Traceability and Preservation

The application MUST preserve original remote paths, revisions, metadata, and
licenses whenever those values are available. Manifest updates MUST be atomic
and resumable. Credentials such as `HF_TOKEN` MUST be read from the environment
or ignored local configuration and MUST NOT be logged, committed, or embedded
in generated artifacts. Changes to data contracts MUST document migration or
compatibility consequences.

Traceability is part of the research result, not an optional operational detail.

### V. Maintainable Simplicity

Code MUST favor small modules, explicit contracts, clear names, and narrow
interfaces. The CLI, acquisition coordination, configuration, and external
Hugging Face integration SHOULD remain separately testable. New dependencies,
concurrency, retries, or abstractions MUST have a documented reason and tests
for their failure modes. Implementations SHOULD follow YAGNI: do not add a
framework, layer, or feature before a current requirement needs it.

The project is a research tool; understandability and reliable change are more
valuable than speculative generality.

## Project Constraints

- The application root is `../app/`; the current implementation is a Python CLI
  named `libras` for reproducible Libras dataset acquisition.
- Datasets are stored under `../app/data/`; source code and tests are under
  `../app/dataset/`.
- Hugging Face access MUST use the official client integration and a resolved
  revision. The default test path MUST remain independent of Hugging Face.
- `specs/` is the canonical location for feature specifications,
  plans, data models, quickstarts, and task lists.
- Generated graph artifacts belong to `graphify-out/`; a second graph output
  under `../app/` MUST NOT be created.

## Development Workflow and Quality Gates

1. Establish or update the feature specification before implementation.
2. Record technical decisions and verify the constitution before planning.
3. Create dependency-ordered tasks that distinguish existing behavior from
   missing behavior.
4. Implement only tasks that are not already satisfied by the codebase.
5. Run the documented test suite and relevant CLI checks before declaring the
   feature complete.
6. Review documentation, manifests, credentials, and generated artifacts for
   accidental leakage or scope violations.
7. Keep changes on a `feature/<slug>` branch. Never commit directly to
   `main` or `develop`; the first promotion goes through `develop`.

The quality gate fails when a requirement has no verification method, when a
test cannot run because its dependency is undeclared, or when an implementation
changes a persisted manifest contract without documenting the consequence.

## Governance

This constitution governs application changes and takes precedence over
convenience practices that conflict with it. Amendments MUST state the reason,
the affected principles, the compatibility impact, and any migration work.
Every amendment MUST update the semantic version and amendment date. Major
versions remove or redefine obligations; minor versions add or materially
expand obligations; patch versions clarify wording without changing intent.

Feature reviews MUST check the applicable principles, tests, documentation,
data traceability, and application/harness boundary. Any exception MUST be
recorded in the feature plan with its rationale, risk, and expiration or
follow-up task.

**Version**: 1.0.0 | **Ratified**: 2026-10-11 | **Last Amended**: 2026-10-11
