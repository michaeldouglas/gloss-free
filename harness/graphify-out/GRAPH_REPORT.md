# Graph Report - harness  (2026-10-04)

## Corpus Check
- 173 files · ~136,732 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 1758 nodes · 2274 edges · 188 communities (145 shown, 43 thin omitted)
- Extraction: 94% EXTRACTED · 6% INFERRED · 0% AMBIGUOUS · INFERRED: 136 edges (avg confidence: 0.87)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `87be6ef3`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- ValueError
- _tabular.py
- CliError
- review_template.md
- Effect Sizes and Power Analysis
- Literature Review (ML / Statistics)
- hardware_probe.py
- Statistical Reporting Standards
- Implementation Plan: Estruturar Projeto App
- 1. Comparing Groups
- Research Systematic Literature Review
- Tasks: [FEATURE NAME]
- validate_review_pack.py
- speckit-analyze/SKILL.md
- Implementation Plan: Padronizar Aprovação de Slug
- openvino_installer.py
- Analytics and Data Analysis
- DOCX Research Guide — 8 Sections + Technical Requirements
- read_openvino_docs.py
- paper_context_artifacts.py
- translate_pdf_layout.py
- app::huggingface_hub_errors
- arxiv_search.py
- General Scientific Formats and EDA Rigor
- Workflow
- app::concurrent_futures
- citation_tracker.py
- Exploratory Data Analysis Report
- bounded_file_limit
- Review Protocol
- ML / Statistics Venue Tier Reference
- Paper-Context Evidence Map Template
- Microscopy and Scientific Imaging Formats
- Exploratory Data Analysis
- Execution Steps
- common.ps1
- Proteomics and Metabolomics Formats
- _capabilities.py
- display_identifier
- Statistical Analysis
- Bioinformatics and Genomics Formats
- Litreview — Academic Literature Orientation
- eda_analyzer.py
- Corpus Adequacy Assessment
- aggregate.py
- Feature Specification: [FEATURE NAME]
- Chemistry and Molecular Formats
- Spectroscopy and Analytical Chemistry Formats
- {Report Title}
- Search Budget Allocation — Quick / Standard / Deep + Cross-Search Intelligence
- Systematic Literature Review Skill
- Standards
- _main
- new_notebook.py
- Jupyter Notebook Skill
- Source Card: {source_id}
- Protocol Template
- speckit-plan/SKILL.md
- app::typer_testing
- speckit-specify/SKILL.md
- speckit-tasks/SKILL.md
- Statistical Assumptions and Diagnostic Procedures
- app::pkg_huggingface_hub
- Bayesian Statistical Analysis
- Core Principles
- Core Principles
- inspect_manifest
- _main
- _main
- model_converter.py
- Supplemental Gap Search
- Framework Selection — PICO, SPIDER, Decomposition, Hybrid
- Scientific Data Analysis Coordinator
- extract_pdf_text.py
- Prose Hygiene (no AI tells)
- free_search.py
- Subagente coordenador de revisão de literatura
- Implementation Plan: [FEATURE]
- Review Workflow Data Schema
- Search Strategy
- extract_pdf_front_matter.py
- framework_recommender.py
- Adversarial Literature Checklist
- Search Strategy Template
- speckit-checklist/SKILL.md
- Decisões
- AGENTS.md
- verify_citations.py
- Domain Adapters
- PRISMA 2020 Core Checklist (Operational)
- Literature Discovery and Recall Assurance Contract
- speckit-clarify/SKILL.md
- speckit-implement/SKILL.md
- PDF Translation Coordinator
- Quickstart de Validação: Padronizar Aprovação de Slug
- Artefatos
- Quickstart: Estruturar Projeto App
- Intel Hardware Advisor
- Intel OpenVINO Installer
- Prompt: Source Intake Triage
- register_sources.py
- search_pubmed.py
- Anti-Patterns
- Checkpoint (grill-me forcing-options moment)
- Screening Template
- speckit-constitution/SKILL.md
- Example Report Templates
- create-new-feature.ps1
- Entidades
- Intel Docs Reader
- OpenVINO Installation Methods
- Included Source Card Index
- create_review_matrices.py
- validate_citation_ledger.py
- main
- PDF translation with layout preservation
- speckit-taskstoissues/SKILL.md
- Test-Specific Assumptions
- Running Statistical Tests
- [CHECKLIST TYPE] Checklist: [FEATURE NAME]
- Intel OpenVINO Benchmark
- Intel OpenVINO GenAI Runner
- inference_runner.py
- Intel OpenVINO Inference Runner
- Intel OpenVINO Model Converter
- Intel OpenVINO Model Optimizer
- Intel OpenVINO Model Server
- Prompt: APA Report Writer
- Prompt: Citation Audit
- Prompt: Corpus Adequacy Assessment
- Prompt: Evidence Extraction
- Prompt: Review Framing
- Prompt: Search And Selection
- Prompt: Source Card Generation
- Prompt: Synthesis
- search_crossref.py
- search_openalex.py
- search_semantic_scholar.py
- Cross-Search Intelligence
- Phase 3: Targeted Searches
- Phase 0: Grill-Me Intake (3 forcing questions, one at a time)
- Evidence Table Template
- Common Assumptions Across Tests
- Effect Sizes
- benchmark_runner.py
- genai_runner.py
- model_optimizer.py
- model_server.py
- Bundled Resources
- __init__.py
- evidence-guide.md
- benchmark-methodology.md
- genai-workflows.md
- inference-modes.md
- model-preparation.md
- optimization-methods.md
- server-workflows.md
- experiment-patterns.md
- notebook-structure.md
- quality-checklist.md
- tutorial-patterns.md
- app::dataclasses
- app::datetime
- app::dotenv
- app::huggingface_hub
- app::json
- app::logging
- app::os
- app::pathlib
- app::pkg_python_dotenv
- app::pkg_rich
- app::pkg_typer
- app::rich_console
- app::rich_progress
- app::rich_table
- app::tempfile
- app::threading
- app::time
- app::tqdm
- app::typer
- app::typing
- app::unittest
- app::unittest_mock

## God Nodes (most connected - your core abstractions)
1. `CliError` - 41 edges
2. `checked_input_file()` - 20 edges
3. `Exploratory Data Analysis Report` - 16 edges
4. `Review Protocol` - 16 edges
5. `Litreview — Academic Literature Orientation` - 15 edges
6. `Statistical Analysis` - 15 edges
7. `main()` - 14 edges
8. `DOCX Research Guide — 8 Sections + Technical Requirements` - 14 edges
9. `emit_json()` - 13 edges
10. `_build_report()` - 13 edges

## Surprising Connections (you probably didn't know these)
- `suffix_key()` --uses--> `CliError`  [INFERRED]
  .agents/skills/exploratory-data-analysis/scripts/_capabilities.py → .agents/skills/exploratory-data-analysis/scripts/_common.py
- `inspect_manifest()` --calls--> `capability_for_path()`  [INFERRED]
  .agents/skills/exploratory-data-analysis/scripts/capability_manifest.py → .agents/skills/exploratory-data-analysis/scripts/_capabilities.py
- `_main()` --calls--> `capability_for_path()`  [INFERRED]
  .agents/skills/exploratory-data-analysis/scripts/distribution_sensitivity.py → .agents/skills/exploratory-data-analysis/scripts/_capabilities.py
- `build_report()` --calls--> `capability_for_path()`  [INFERRED]
  .agents/skills/exploratory-data-analysis/scripts/eda_analyzer.py → .agents/skills/exploratory-data-analysis/scripts/_capabilities.py
- `_main()` --calls--> `capability_for_path()`  [INFERRED]
  .agents/skills/exploratory-data-analysis/scripts/image_inspector.py → .agents/skills/exploratory-data-analysis/scripts/_capabilities.py

## Import Cycles
- None detected.

## Communities (188 total, 43 thin omitted)

### Community 0 - "ValueError"
Cohesion: 0.10
Nodes (45): evidence(), Inputs, main(), parser(), protocol(), ArgumentParser, Namespace, recall_audit() (+37 more)

### Community 1 - "_tabular.py"
Cohesion: 0.07
Nodes (38): finite_number(), Parse a finite decimal number without evaluating expressions., audit_distributions(), audit_missingness_and_leakage(), ColumnAccumulator, delimiter_for_path(), _distribution_report(), is_missing() (+30 more)

### Community 2 - "CliError"
Cohesion: 0.13
Nodes (37): _absolute_lexical(), atomic_write_bytes(), bounded_integer(), checked_input_file(), checked_output_file(), checked_root(), CliError, emit_json() (+29 more)

### Community 3 - "review_template.md"
Cohesion: 0.05
Nodes (37): 1.1 Motivation, 1.2 Scope and contribution, 1.3 Related surveys, 1. Introduction, 2.1 Research questions (PMDB frame), 2.2 Inclusion and exclusion criteria, 2.3 Search strategy, 2.4 Screening (PRISMA-style flow) (+29 more)

### Community 4 - "Effect Sizes and Power Analysis"
Cohesion: 0.05
Nodes (37): A Priori Power Analysis (Planning), Adjusted R², ANOVA, APA Style Guidelines, Bayes Factor (BF), Bayesian Evidence (Not an Effect Size), Bootstrap Confidence Intervals, Categorical Data Analysis (+29 more)

### Community 5 - "Literature Review (ML / Statistics)"
Cohesion: 0.06
Nodes (35): Best Practices, Bundled Resources, Citation Count Thresholds (ML/Stats Adjusted), Common Pitfalls, Core Workflow, Dependencies, Document the search, Example: Operator Learning for PDEs Review (+27 more)

### Community 6 - "hardware_probe.py"
Cohesion: 0.13
Nodes (33): collect_additional_configurations(), collect_live(), collect_openvino(), collect_platform(), _configuration(), _device_type(), _has_device_node(), _is_container() (+25 more)

### Community 7 - "Statistical Reporting Standards"
Cohesion: 0.06
Nodes (34): Additional Resources, Always Report, ANOVA, Assumption Checks, Bayesian Statistics, Checklist for Statistical Reporting, Chi-Square Tests, Common Mistakes to Avoid (+26 more)

### Community 8 - "Implementation Plan: Estruturar Projeto App"
Cohesion: 0.06
Nodes (28): Content Quality, Feature Readiness, Notes, Requirement Completeness, Specification Quality Checklist: Estruturar Projeto App, Complexity Tracking, Constitution Check, Documentation (this feature) (+20 more)

### Community 9 - "1. Comparing Groups"
Cohesion: 0.07
Nodes (28): 1. Comparing Groups, 2. Relationships Between Variables, 3. Agreement and Reliability, 4. Categorical Data Analysis, 5. Bayesian Alternatives, Agreement Between Methods, Binary Outcome, Contingency Tables (+20 more)

### Community 10 - "Research Systematic Literature Review"
Cohesion: 0.07
Nodes (26): 10) Validate and report assurance, 1) Define protocol and domain adapter, 2) Build coverage map and seeds, 3) Execute multi-channel discovery, 4) Repair search and audit recall, 5) Close coverage questions and freeze the candidate corpus, 6) Screen and resolve publication versions, 7) Extract structured evidence (+18 more)

### Community 11 - "Tasks: [FEATURE NAME]"
Cohesion: 0.07
Nodes (26): Dependencies & Execution Order, Format: `[ID] [P?] [Story] Description`, Implementation for User Story 1, Implementation for User Story 2, Implementation for User Story 3, Implementation Strategy, Incremental Delivery, MVP First (User Story 1 Only) (+18 more)

### Community 12 - "validate_review_pack.py"
Cohesion: 0.21
Nodes (24): meaningful(), Any, Validate canonical questions and reciprocal search/record/amendment links., split_ids(), unresolved_high_priority_novelty_questions(), validate_coverage_questions(), main(), parse_non_negative() (+16 more)

### Community 13 - "speckit-analyze/SKILL.md"
Cohesion: 0.08
Nodes (25): 1. Initialize Analysis Context, 2. Load Artifacts (Progressive Disclosure), 3. Build Semantic Models, 4. Detection Passes (Token-Efficient Analysis), 5. Severity Assignment, 6. Produce Compact Analysis Report, 7. Provide Next Actions, 8. Offer Remediation (+17 more)

### Community 14 - "Implementation Plan: Padronizar Aprovação de Slug"
Cohesion: 0.08
Nodes (23): Content Quality, Feature Readiness, Notes, Requirement Completeness, Specification Quality Checklist: Padronizar Aprovação de Slug, Complexity Tracking, Constitution Check, Documentation (this feature) (+15 more)

### Community 15 - "openvino_installer.py"
Cohesion: 0.22
Nodes (24): _action(), _available(), _build_actions(), _build_report(), _compatible(), _detect_context(), _exact_version(), _live_verify() (+16 more)

### Community 16 - "Analytics and Data Analysis"
Cohesion: 0.08
Nodes (23): Accessibility in Visualizations, Analytics and Data Analysis, Analytics Implementation, Code Organization, Core Dependencies, Data Analysis with Pandas, Data Manipulation Best Practices, Data Validation (+15 more)

### Community 17 - "DOCX Research Guide — 8 Sections + Technical Requirements"
Cohesion: 0.09
Nodes (23): 4a. What the Research Shows, 4b. Key Papers, 4c. Key Search Terms, 4d. Boolean Search Strings, Anti-Patterns, Citations (7 sources), DOCX Research Guide — 8 Sections + Technical Requirements, DOCX Technical Requirements (+15 more)

### Community 18 - "read_openvino_docs.py"
Cohesion: 0.17
Nodes (15): default_cache_dir(), _download(), ensure_snapshot(), _excerpt(), _extract_archive(), _HtmlTextParser, inspect_cache(), main() (+7 more)

### Community 19 - "paper_context_artifacts.py"
Cohesion: 0.24
Nodes (19): _build_parser(), _context_md(), _decision_json(), _evidence_table_md(), _first_table_header(), init_artifacts(), _is_rating(), _load_json() (+11 more)

### Community 20 - "translate_pdf_layout.py"
Cohesion: 0.25
Nodes (18): clean_source(), clean_translation(), correct_fragment(), get_blocks(), image_rects(), insert_fitted(), insertion_rect(), is_heading() (+10 more)

### Community 22 - "arxiv_search.py"
Cohesion: 0.14
Nodes (15): _build_parser(), _build_search_query(), main(), _normalise_arxiv_id(), _parse_entry(), Any, ArgumentParser, Build arXiv's `search_query` field. arXiv uses its own query grammar: `ti:`,… (+7 more)

### Community 23 - "General Scientific Formats and EDA Rigor"
Cohesion: 0.11
Nodes (17): Authoritative sources, Bundled approach, Capability boundary, CSV and TSV, Excel, General Scientific Formats and EDA Rigor, HDF5 and h5py, NumPy NPY and NPZ (+9 more)

### Community 24 - "Workflow"
Cohesion: 0.11
Nodes (17): 1. Frame The Review, 2. Register Sources, 3. Triage Sources, 4. Assess Corpus Adequacy, 5. Extract Evidence, 6. Code And Synthesize, 7. Draft The Report, 8. Audit Citations (+9 more)

### Community 26 - "citation_tracker.py"
Cohesion: 0.36
Nodes (17): action_close(), action_list(), action_record_cited(), action_record_papers_received(), action_record_search(), action_start(), action_status(), load_session() (+9 more)

### Community 27 - "Exploratory Data Analysis Report"
Cohesion: 0.12
Nodes (16): Analysis status, Data dictionary and measurement context, Distributions and outlier sensitivity, Exploratory comparisons and multiplicity, Exploratory Data Analysis Report, Key findings, Limitations, Missingness, censoring, and detection limits (+8 more)

### Community 28 - "bounded_file_limit"
Cohesion: 0.17
Nodes (14): bounded_file_limit(), Run a CLI body with concise expected-error handling., Validate a caller-selected byte limit against the hard ceiling., run_cli(), build_parser(), _main(), ArgumentParser, build_parser() (+6 more)

### Community 29 - "Review Protocol"
Cohesion: 0.12
Nodes (16): Audience, Coding Approach, Corpus Adequacy Check, Evidence Base, Exclusion Criteria, Extraction Focus, Guiding Question, Human Review Gates (+8 more)

### Community 30 - "ML / Statistics Venue Tier Reference"
Cohesion: 0.12
Nodes (16): How to use these tiers in a review, Industry / Engineering Venues (treat carefully), Machine Learning (general / methodological), ML / Statistics Venue Tier Reference, Scientific Machine Learning / Operator Learning / Computational Science, Statistics, Tier 1, Tier 1 — Top general ML (+8 more)

### Community 31 - "Paper-Context Evidence Map Template"
Cohesion: 0.12
Nodes (16): Benchmark Or Evaluation Context, Claims That Need Qualification, Closest Prior Work, Confidence and Limitations, Impact / Significance Context, Inclusion Decisions, literature-context-decision.json, literature-context-evidence-table.md (+8 more)

### Community 32 - "Microscopy and Scientific Imaging Formats"
Cohesion: 0.12
Nodes (15): Authoritative sources, DICOM, Exact capability matrix, Imaging EDA rigor, Interpret carefully, Metadata-only safety model, Microscopy and Scientific Imaging Formats, NIfTI (+7 more)

### Community 33 - "Exploratory Data Analysis"
Cohesion: 0.12
Nodes (15): 1. Confirm authorization and root, 2. Manifest before content analysis, 3. Run the narrowest automated tool, 4. Add scientific context, 5. Create the report scaffold, Citing Scientific Agent Skills, Exact capability matrix, Exploratory Data Analysis (+7 more)

### Community 34 - "Execution Steps"
Cohesion: 0.12
Nodes (15): 1. Initialize Convergence Context, 2. Load Artifacts (Progressive Disclosure), 3. Build the Intent Inventory, 4. Assess the Codebase and Classify Findings, 5. Assign Severity, 6. Present the In-Session Findings Summary, 7. Append Convergence Tasks (or report converged), 8. Provide Next Actions (Handoff) (+7 more)

### Community 35 - "common.ps1"
Cohesion: 0.23
Nodes (13): Find-SpecifyRoot(), Format-SpecKitCommand(), Get-CurrentBranch(), Get-FeaturePathsEnv(), Get-InvokeSeparator(), Get-NormalizedPriority(), Get-Python3Command(), Get-RepoRoot() (+5 more)

### Community 36 - "Proteomics and Metabolomics Formats"
Cohesion: 0.13
Nodes (14): Authoritative sources, Design, leakage, and inference, Distribution and outlier sensitivity, Exact capability boundary, HDF5 and related containers, Identification formats, Missingness, censoring, and limits, mzIdentML (+6 more)

### Community 37 - "_capabilities.py"
Cohesion: 0.21
Nodes (13): automated_capability_rows(), capability_for_path(), _first_nonempty_text_byte(), preflight_npz(), Any, Path, Return a registered compound or simple suffix, failing closed otherwise., Return a copy of the closed capability entry for a path. (+5 more)

### Community 38 - "display_identifier"
Cohesion: 0.28
Nodes (14): display_identifier(), Reveal a sanitized identifier only after explicit caller opt-in., _array_report(), _dtype_report(), inspect_hdf5(), inspect_json(), inspect_numpy(), Any (+6 more)

### Community 39 - "Statistical Analysis"
Cohesion: 0.13
Nodes (15): A Priori Power Analysis (Study Planning), Analysis Workflow, Assumption Checking, Bayesian Statistics, Citing Scientific Agent Skills, Installation, Overview, Power Analysis (+7 more)

### Community 40 - "Bioinformatics and Genomics Formats"
Cohesion: 0.14
Nodes (13): Appropriate next checks, Authoritative sources, Bioinformatics and Genomics Formats, EDA rigor for genomic data, Exact capability matrix, FASTA, FASTQ, H5AD, Loom, and Matrix Market (+5 more)

### Community 41 - "Litreview — Academic Literature Orientation"
Cohesion: 0.14
Nodes (14): Agent Integrity Rules (Research-Pack Convention), Anti-Patterns To Reject, Cross-Search Intelligence, DOCX Technical Requirements, Error Handling, Free-lane URL templates (exact), Litreview — Academic Literature Orientation, Output (+6 more)

### Community 42 - "eda_analyzer.py"
Cohesion: 0.26
Nodes (12): analyze_file(), build_parser(), build_report(), _infer_output_format(), _main(), markdown_report(), Any, ArgumentParser (+4 more)

### Community 43 - "Corpus Adequacy Assessment"
Cohesion: 0.15
Nodes (12): Corpus Adequacy Assessment, Corpus Snapshot, Coverage By Review Need, Date, Judgment, Need 1, Need 2, Need 3 (+4 more)

### Community 44 - "aggregate.py"
Cohesion: 0.28
Nodes (12): deduplicate(), filter_min_citations(), filter_year(), format_markdown(), load_papers(), main(), merge_records(), normalize_arxiv_id() (+4 more)

### Community 45 - "Feature Specification: [FEATURE NAME]"
Cohesion: 0.15
Nodes (12): Assumptions, Edge Cases, Feature Specification: [FEATURE NAME], Functional Requirements, Key Entities *(include if feature involves data)*, Measurable Outcomes, Requirements *(mandatory)*, Success Criteria *(mandatory)* (+4 more)

### Community 46 - "Chemistry and Molecular Formats"
Cohesion: 0.17
Nodes (11): Authoritative sources, Capability boundary, Chemistry and Molecular Formats, Chemistry EDA rigor, HDF5, NumPy, and tabular chemistry exports, Molecular dynamics trajectories, Molfile, SDF, and line notations, PDB and PDBx/mmCIF (+3 more)

### Community 47 - "Spectroscopy and Analytical Chemistry Formats"
Cohesion: 0.17
Nodes (11): Analytical EDA rigor, Authoritative sources, Capability boundary, Chromatography and thermal/electrochemical exports, Detection limits and censoring, JCAMP-DX, mzML and related mass-spectrometry formats, NMR data (+3 more)

### Community 48 - "{Report Title}"
Cohesion: 0.17
Nodes (11): Appendix: Source Table or Review Matrix, Conclusion, Discussion, Executive Summary, Gaps and Future Research, Introduction and Review Purpose, References, {Report Title} (+3 more)

### Community 49 - "Search Budget Allocation — Quick / Standard / Deep + Cross-Search Intelligence"
Cohesion: 0.17
Nodes (12): Anti-Patterns, Citations (7 sources), Deep Dive (20 searches), Lane Check (Replaces Plan-Tier Detection), Operational Checklist, Quick Scan (5 searches), Search Budget Allocation — Quick / Standard / Deep + Cross-Search Intelligence, Sequential Execution Discipline (+4 more)

### Community 50 - "Systematic Literature Review Skill"
Cohesion: 0.17
Nodes (11): Examples, Notes, Overview, Phase 1: Plan, Phase 2: Search arXiv, Phase 3: Extract metadata in parallel, Phase 4: Synthesize and format, Phase 5: Save and present (+3 more)

### Community 51 - "Standards"
Cohesion: 0.18
Nodes (10): Analyze Data Quality, Automated Test Guidance, Core Checks, Defaults, Output Standards, Related Skills, Severity, Specific Check Guidance (+2 more)

### Community 52 - "_main"
Cohesion: 0.38
Nodes (10): _bounded_element_count(), build_parser(), inspect_image_file(), _inspect_pillow(), _inspect_tiff(), _main(), Any, ArgumentParser (+2 more)

### Community 53 - "new_notebook.py"
Cohesion: 0.36
Nodes (10): default_output(), find_repo_root(), load_template(), main(), parse_args(), Any, Namespace, Path (+2 more)

### Community 54 - "Jupyter Notebook Skill"
Cohesion: 0.18
Nodes (10): Decision tree, Dependencies (install only when needed), Environment, Jupyter Notebook Skill, Reference map, Skill path (set once), Temp and output conventions, Templates and helper script (+2 more)

### Community 55 - "Source Card: {source_id}"
Cohesion: 0.18
Nodes (10): Citation, Ingestion Status, Limitations, Methods or Approach, Notes for Future Retrieval, Purpose of Source, Raw Source, Relevance to Current Review (+2 more)

### Community 56 - "Protocol Template"
Cohesion: 0.18
Nodes (10): Assumptions applied, Core question, Deviations log, Eligibility criteria, Exclusion criteria, Inclusion criteria, Metadata, Outcomes and endpoints (+2 more)

### Community 57 - "speckit-plan/SKILL.md"
Cohesion: 0.18
Nodes (10): Completion Report, Done When, Key rules, Mandatory Post-Execution Hooks, Outline, Phase 0: Outline & Research, Phase 1: Design & Contracts, Phases (+2 more)

### Community 59 - "speckit-specify/SKILL.md"
Cohesion: 0.18
Nodes (10): Completion Report, Done When, For AI Generation, Mandatory Post-Execution Hooks, Outline, Pre-Execution Checks, Quick Guidelines, Section Requirements (+2 more)

### Community 60 - "speckit-tasks/SKILL.md"
Cohesion: 0.18
Nodes (10): Checklist Format (REQUIRED), Completion Report, Done When, Mandatory Post-Execution Hooks, Outline, Phase Structure, Pre-Execution Checks, Task Generation Rules (+2 more)

### Community 61 - "Statistical Assumptions and Diagnostic Procedures"
Cohesion: 0.18
Nodes (8): Current API sources, Design-specific planning, General Principles, Outlier Detection, Reporting Assumption Checks, Sample Size Considerations, Small Sample Considerations, Statistical Assumptions and Diagnostic Procedures

### Community 63 - "Bayesian Statistical Analysis"
Cohesion: 0.18
Nodes (11): Bayesian Statistical Analysis, Correlation with uncertainty in location and scale, Credible intervals and practical equivalence, Diagnostics and posterior predictive checks, Hierarchical group comparisons / Bayesian ANOVA, Model comparison, Primary API sources, Questions, priors and uncertainty (+3 more)

### Community 64 - "Core Principles"
Cohesion: 0.18
Nodes (10): Core Principles, Governance, [PRINCIPLE_1_NAME], [PRINCIPLE_2_NAME], [PRINCIPLE_3_NAME], [PRINCIPLE_4_NAME], [PRINCIPLE_5_NAME], [PROJECT_NAME] Constitution (+2 more)

### Community 65 - "Core Principles"
Cohesion: 0.18
Nodes (10): Core Principles, Governance, [PRINCIPLE_1_NAME], [PRINCIPLE_2_NAME], [PRINCIPLE_3_NAME], [PRINCIPLE_4_NAME], [PRINCIPLE_5_NAME], [PROJECT_NAME] Constitution (+2 more)

### Community 66 - "inspect_manifest"
Cohesion: 0.29
Nodes (9): build_parser(), capability_matrix(), inspect_manifest(), _main(), Any, ArgumentParser, Path, Build a redacted manifest from a previously checked local file. (+1 more)

### Community 67 - "_main"
Cohesion: 0.24
Nodes (9): markdown_scalar(), Bound and neutralize an explicitly requested untrusted identifier., Return a bounded scalar that cannot introduce Markdown structure., sanitize_identifier(), build_parser(), _main(), ArgumentParser, Fill only trusted scalar placeholders in the bundled template. (+1 more)

### Community 68 - "_main"
Cohesion: 0.24
Nodes (9): Return a deterministic pseudonymous token; this is not anonymization., stable_token(), build_parser(), inspect_sequence_file(), _main(), Any, ArgumentParser, Path (+1 more)

### Community 69 - "model_converter.py"
Cohesion: 0.33
Nodes (8): action(), build_report(), detect_context(), infer_framework(), load_fixture(), main(), Namespace, redact()

### Community 70 - "Supplemental Gap Search"
Cohesion: 0.20
Nodes (9): Candidate Exclusion Rules, Candidate Inclusion Priority, Database Order, Purpose, Search Strings, Stopping Rule, Supplemental Gap Search, Target Concepts (+1 more)

### Community 71 - "Framework Selection — PICO, SPIDER, Decomposition, Hybrid"
Cohesion: 0.20
Nodes (10): Citations (7 sources), Decomposition (technology / engineering), Framework Selection — PICO, SPIDER, Decomposition, Hybrid, Hybrid (cross-cutting), Operational Checklist, PICO (default), SPIDER (social / qualitative), The Core Claim (+2 more)

### Community 72 - "Scientific Data Analysis Coordinator"
Cohesion: 0.20
Nodes (9): Data integrity invariants, Handoff, Later stages, Notebook deliverables, Repository and Git protocol, Role, Routing policy, Scientific Data Analysis Coordinator (+1 more)

### Community 73 - "extract_pdf_text.py"
Cohesion: 0.42
Nodes (8): clean(), extract_pdf_text(), main(), Path, Extract full text from registered PDF sources. Use this after triage,…, resolve_source_path(), safe_name(), wanted()

### Community 74 - "Prose Hygiene (no AI tells)"
Cohesion: 0.22
Nodes (8): A. Phrase-level cuts, B. Structural tells (the strongest "AI smell" in surveys), C. Rhythm — break the paper-by-paper cadence, D. Survey-specific discipline, E. Academic exceptions (relax these stop-slop rules), Per-paragraph checklist (fast pass), Precedence, Prose Hygiene (no AI tells)

### Community 75 - "free_search.py"
Cohesion: 0.36
Nodes (8): _get_json(), main(), GET a JSON document with a polite User-Agent and a hard timeout., PubMed E-utilities: esearch (PMIDs) -> esummary (metadata)., OpenAlex works search. mailto joins the polite pool (recommended)., render_human(), search_openalex(), search_pubmed()

### Community 76 - "Subagente coordenador de revisão de literatura"
Cohesion: 0.22
Nodes (8): Escolha da skill, Fluxo de branch e Pull Request, Integridade da revisão, Papel, Preservação obrigatória do trabalho anterior, Regra de roteamento entre as skills de RSL, Subagente coordenador de revisão de literatura, Sugestão e aprovação obrigatórias antes de alterar arquivos

### Community 77 - "Implementation Plan: [FEATURE]"
Cohesion: 0.22
Nodes (8): Complexity Tracking, Constitution Check, Documentation (this feature), Implementation Plan: [FEATURE], Project Structure, Source Code (repository root), Summary, Technical Context

### Community 78 - "Review Workflow Data Schema"
Cohesion: 0.25
Nodes (7): Corpus Adequacy Rule, Evidence States, Required Identifiers, Required Tables, Review Workflow Data Schema, Traceability Rule, Triage Rule

### Community 79 - "Search Strategy"
Cohesion: 0.25
Nodes (7): Candidate Recording Rules, Database Order, Fallback Search Strings, Primary Search String, Search Logging Rules, Search Strategy, Stopping Rule

### Community 80 - "extract_pdf_front_matter.py"
Cohesion: 0.50
Nodes (7): clean(), extract_front_matter(), main(), Path, Extract PDF metadata and first pages from registered sources. This script is…, read_front_matter(), resolve_source_path()

### Community 81 - "framework_recommender.py"
Cohesion: 0.43
Nodes (7): count_signals(), generate_starter_questions(), main(), Any, Template-driven sub-area starter questions per framework., recommend(), render_human()

### Community 82 - "Adversarial Literature Checklist"
Cohesion: 0.25
Nodes (7): Adversarial Literature Checklist, Claim integrity, Evidence integrity, External validity and failure modes, Final red-team output, Method integrity, Statistical and practical significance

### Community 83 - "Search Strategy Template"
Cohesion: 0.25
Nodes (7): Coverage notes, Deduplication ledger, Query ledger, Search metadata, Search Strategy Template, Version resolution ledger (preprint -> published/venue record), Zotero library sync

### Community 84 - "speckit-checklist/SKILL.md"
Cohesion: 0.25
Nodes (7): Anti-Examples: What NOT To Do, Checklist Purpose: "Unit Tests for English", Example Checklist Types & Sample Items, Execution Steps, Post-Execution Checks, Pre-Execution Checks, User Input

### Community 85 - "Decisões"
Cohesion: 0.25
Nodes (7): Decisão: implementar a regra nas instruções do subagente, Decisão: manter a política de branches existente, Decisão: normalizar slugs inválidos e pedir aprovação da versão normalizada, Decisão: usar uma confirmação explícita do slug antes de qualquer mutação, Decisões, Escopo da pesquisa, Research: Padronizar Aprovação de Slug

### Community 86 - "AGENTS.md"
Cohesion: 0.29
Nodes (6): Escopo do projeto, Fluxo Git e subagente de pesquisa, graphify, Preservação de trabalho ao iniciar uma nova feature, Skills locais de revisão de literatura, Tradução de PDFs com preservação de layout

### Community 87 - "verify_citations.py"
Cohesion: 0.48
Nodes (6): consistency_check(), fetch_arxiv_meta(), fetch_crossref_meta(), find_citations(), main(), Yield (kind, id, line_no, context).

### Community 88 - "Domain Adapters"
Cohesion: 0.29
Nodes (6): AI/ML adapter, Biomedical adapter, Domain Adapters, Generic bias rubric, Policy and governance adapter, Social science adapter

### Community 89 - "PRISMA 2020 Core Checklist (Operational)"
Cohesion: 0.29
Nodes (6): Bias and confidence, Data extraction and synthesis, Discovery and selection, PRISMA 2020 Core Checklist (Operational), Protocol and scope, Reproducibility

### Community 90 - "Literature Discovery and Recall Assurance Contract"
Cohesion: 0.29
Nodes (6): Corpus manifest, Hard failures, Literature Discovery and Recall Assurance Contract, Recall-audit artifact, Required assurance for systematic profiles, Review profiles

### Community 91 - "speckit-clarify/SKILL.md"
Cohesion: 0.29
Nodes (6): Completion Report, Done When, Mandatory Post-Execution Hooks, Outline, Pre-Execution Checks, User Input

### Community 92 - "speckit-implement/SKILL.md"
Cohesion: 0.29
Nodes (6): Completion Report, Done When, Mandatory Post-Execution Hooks, Outline, Pre-Execution Checks, User Input

### Community 93 - "PDF Translation Coordinator"
Cohesion: 0.29
Nodes (6): Before mutation, Execution, PDF Translation Coordinator, Role, Scope, Validation and handoff

### Community 94 - "Quickstart de Validação: Padronizar Aprovação de Slug"
Cohesion: 0.29
Nodes (6): Cenário 1 — sugestão antes da alteração, Cenário 2 — rejeição e nova proposta, Cenário 3 — integridade dos artefatos, Critério de conclusão, Pré-requisitos, Quickstart de Validação: Padronizar Aprovação de Slug

### Community 95 - "Artefatos"
Cohesion: 0.29
Nodes (6): Aplicação, Artefatos, Data Model: Estruturar Projeto App, Harness, Procedimento de validação, Relacionamentos

### Community 96 - "Quickstart: Estruturar Projeto App"
Cohesion: 0.29
Nodes (6): Executar a verificação mínima, Falhas esperadas, Pré-requisitos, Próxima fase, Quickstart: Estruturar Projeto App, Validar a separação dos diretórios

### Community 97 - "Intel Hardware Advisor"
Cohesion: 0.33
Nodes (5): Intel Hardware Advisor, Interpret it, Maintainer validation, Safety boundaries, Use

### Community 98 - "Intel OpenVINO Installer"
Cohesion: 0.33
Nodes (5): Intel OpenVINO Installer, Method routing, Output, Safety boundaries, Workflow

### Community 99 - "Prompt: Source Intake Triage"
Cohesion: 0.33
Nodes (5): Fit Classes, Instruction, Prompt: Source Intake Triage, Required Output, Rules

### Community 100 - "register_sources.py"
Cohesion: 0.60
Nodes (5): main(), make_source_id(), Path, Register raw source files into a source inventory CSV. Usage: python…, register_sources()

### Community 101 - "search_pubmed.py"
Cohesion: 0.60
Nodes (5): efetch_batch(), esearch(), main(), parse_xml(), _text()

### Community 102 - "Anti-Patterns"
Cohesion: 0.33
Nodes (6): Anti-Patterns, Defaulting to PICO without justification, Forcing the framework to fit, Hybrid for everything, Ignoring the recommender's recommendation, Picking framework before reading Q1

### Community 103 - "Checkpoint (grill-me forcing-options moment)"
Cohesion: 0.33
Nodes (6): 3-4 sentence recon summary, Checkpoint (grill-me forcing-options moment), Depth re-confirmation (forcing choice), Framework breakdown table, Sub-area forcing options, Why I'm asking (the rationale)

### Community 104 - "Screening Template"
Cohesion: 0.33
Nodes (5): Decision ledger, Exclusion reasons (full-text stage), Exclusion reasons (title/abstract stage), PRISMA counts, Screening Template

### Community 105 - "speckit-constitution/SKILL.md"
Cohesion: 0.33
Nodes (5): Outline, Post-Execution Checks, Pre-Execution Checks, Scope Guard, User Input

### Community 106 - "Example Report Templates"
Cohesion: 0.33
Nodes (6): Bayesian Analysis, Example Report Templates, Independent T-Test, Multiple Regression, One-Way ANOVA, Reporting Results

### Community 108 - "Entidades"
Cohesion: 0.33
Nodes (5): BranchDecision, Entidades, Modelo de Dados: Padronizar Aprovação de Slug, SlugProposal, Transições

### Community 109 - "Intel Docs Reader"
Cohesion: 0.40
Nodes (4): Behavior, Evidence boundaries, Intel Docs Reader, Use

### Community 110 - "OpenVINO Installation Methods"
Cohesion: 0.40
Nodes (4): Official documentation, OpenVINO Installation Methods, Optional components, Version policy

### Community 111 - "Included Source Card Index"
Cohesion: 0.40
Nodes (4): Current Coverage, Included Source Card Index, Included Sources, Source-Card Status

### Community 112 - "create_review_matrices.py"
Cohesion: 0.60
Nodes (4): create_matrices(), main(), Path, Copy empty review matrix templates into a review-run folder.

### Community 113 - "validate_citation_ledger.py"
Cohesion: 0.60
Nodes (4): main(), Path, Validate that citation ledger rows have source and evidence links., validate()

### Community 114 - "main"
Cohesion: 0.70
Nodes (4): check_deps(), generate(), main(), Path

### Community 115 - "PDF translation with layout preservation"
Cohesion: 0.40
Nodes (4): Non-obvious implementation rules, PDF translation with layout preservation, Required outcome, Workflow

### Community 116 - "speckit-taskstoissues/SKILL.md"
Cohesion: 0.40
Nodes (4): Outline, Post-Execution Checks, Pre-Execution Checks, User Input

### Community 117 - "Test-Specific Assumptions"
Cohesion: 0.40
Nodes (5): ANOVA, Linear Regression, Logistic Regression, T-Tests, Test-Specific Assumptions

### Community 118 - "Running Statistical Tests"
Cohesion: 0.40
Nodes (5): ANOVA with Post-Hoc Tests, Bayesian T-Test, Linear Regression with Diagnostics, Running Statistical Tests, T-Test with Complete Reporting

### Community 119 - "[CHECKLIST TYPE] Checklist: [FEATURE NAME]"
Cohesion: 0.40
Nodes (4): [Category 1], [Category 2], [CHECKLIST TYPE] Checklist: [FEATURE NAME], Notes

### Community 120 - "Intel OpenVINO Benchmark"
Cohesion: 0.50
Nodes (3): Evidence boundaries, Intel OpenVINO Benchmark, Workflow

### Community 121 - "Intel OpenVINO GenAI Runner"
Cohesion: 0.50
Nodes (3): Boundaries, Intel OpenVINO GenAI Runner, Workflow

### Community 122 - "inference_runner.py"
Cohesion: 0.83
Nodes (3): context(), load(), main()

### Community 123 - "Intel OpenVINO Inference Runner"
Cohesion: 0.50
Nodes (3): Device and safety rules, Intel OpenVINO Inference Runner, Workflow

### Community 124 - "Intel OpenVINO Model Converter"
Cohesion: 0.50
Nodes (3): Boundaries, Intel OpenVINO Model Converter, Workflow

### Community 125 - "Intel OpenVINO Model Optimizer"
Cohesion: 0.50
Nodes (3): Boundaries, Intel OpenVINO Model Optimizer, Workflow

### Community 126 - "Intel OpenVINO Model Server"
Cohesion: 0.50
Nodes (3): Boundaries, Intel OpenVINO Model Server, Workflow

### Community 127 - "Prompt: APA Report Writer"
Cohesion: 0.50
Nodes (3): Instruction, Prompt: APA Report Writer, Required Structure

### Community 128 - "Prompt: Citation Audit"
Cohesion: 0.50
Nodes (3): Instruction, Prompt: Citation Audit, Required Output

### Community 129 - "Prompt: Corpus Adequacy Assessment"
Cohesion: 0.50
Nodes (3): Instruction, Prompt: Corpus Adequacy Assessment, Required Output

### Community 130 - "Prompt: Evidence Extraction"
Cohesion: 0.50
Nodes (3): Instruction, Prompt: Evidence Extraction, Required Output

### Community 131 - "Prompt: Review Framing"
Cohesion: 0.50
Nodes (3): Instruction, Prompt: Review Framing, Required Output

### Community 132 - "Prompt: Search And Selection"
Cohesion: 0.50
Nodes (3): Instruction, Prompt: Search And Selection, Required Output

### Community 133 - "Prompt: Source Card Generation"
Cohesion: 0.50
Nodes (3): Instruction, Prompt: Source Card Generation, Required Output

### Community 134 - "Prompt: Synthesis"
Cohesion: 0.50
Nodes (3): Instruction, Prompt: Synthesis, Required Output

### Community 135 - "search_crossref.py"
Cohesion: 0.83
Nodes (3): fetch_page(), main(), normalize()

### Community 136 - "search_openalex.py"
Cohesion: 0.83
Nodes (3): fetch_page(), main(), normalize()

### Community 137 - "search_semantic_scholar.py"
Cohesion: 0.83
Nodes (3): fetch_page(), main(), normalize()

### Community 139 - "Cross-Search Intelligence"
Cohesion: 0.50
Nodes (4): Cross-Search Intelligence, Tracker 1: Repeat-Hit Papers (foundational signal), Tracker 2: Recurring Authors (dominant research group signal), Tracker 3: Citation-Per-Year (seminal-work heuristic)

### Community 140 - "Phase 3: Targeted Searches"
Cohesion: 0.50
Nodes (4): Deep dive (20 searches), Phase 3: Targeted Searches, Quick scan (5 searches), Standard review (10 searches)

### Community 141 - "Phase 0: Grill-Me Intake (3 forcing questions, one at a time)"
Cohesion: 0.50
Nodes (4): Phase 0: Grill-Me Intake (3 forcing questions, one at a time), Q1 (root) — Research question specificity, Q2 (depends on Q1) — Framework hint, Q3 (depends on Q1) — Tentative depth

### Community 142 - "Evidence Table Template"
Cohesion: 0.50
Nodes (3): Evidence Table Template, Extraction guidance, Extraction matrix

### Community 143 - "Common Assumptions Across Tests"
Cohesion: 0.50
Nodes (4): 1. Independence of Observations, 2. Normality, 3. Homogeneity of Variance (Homoscedasticity), Common Assumptions Across Tests

### Community 144 - "Effect Sizes"
Cohesion: 0.50
Nodes (4): Calculating Effect Sizes, Confidence Intervals for Effect Sizes, Effect Sizes, Quick Reference: Common Effect Sizes

### Community 149 - "Bundled Resources"
Cohesion: 0.67
Nodes (3): Bundled Resources, References (`references/`), Scripts (`scripts/`)

## Knowledge Gaps
- **851 isolated node(s):** `Workflow: Exploratory Data Analysis Pipeline`, `Key Principles`, `Quick Start Example`, `Data Manipulation Best Practices`, `Performance Optimization` (+846 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **43 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `CliError` connect `CliError` to `ValueError`, `_tabular.py`, `inspect_manifest`, `_main`, `_main`, `_capabilities.py`, `display_identifier`, `eda_analyzer.py`, `_main`, `bounded_file_limit`?**
  _High betweenness centrality (0.023) - this node is a cross-community bridge._
- **Why does `_load_fixture()` connect `openvino_installer.py` to `ValueError`?**
  _High betweenness centrality (0.006) - this node is a cross-community bridge._
- **Why does `report()` connect `bounded_file_limit` to `ValueError`, `inspect_manifest`, `_main`, `_main`, `eda_analyzer.py`, `_main`?**
  _High betweenness centrality (0.005) - this node is a cross-community bridge._
- **Are the 22 inferred relationships involving `CliError` (e.g. with `preflight_npz()` and `suffix_key()`) actually correct?**
  _`CliError` has 22 INFERRED edges - model-reasoned connections that need verification._
- **Are the 26 inferred relationships involving `ValueError` (e.g. with `_download()` and `ensure_snapshot()`) actually correct?**
  _`ValueError` has 26 INFERRED edges - model-reasoned connections that need verification._
- **Are the 8 inferred relationships involving `checked_input_file()` (e.g. with `_main()` and `_main()`) actually correct?**
  _`checked_input_file()` has 8 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Workflow: Exploratory Data Analysis Pipeline`, `Key Principles`, `Quick Start Example` to the rest of the system?**
  _851 weakly-connected nodes found - possible documentation gaps or missing edges._