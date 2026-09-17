---
name: literature-review-ml
description: Conduct systematic literature reviews for machine learning and statistics research. Searches arXiv, Semantic Scholar, and OpenAlex; tracks ML-specific metadata (datasets, benchmarks, code availability, compute); verifies citations; produces markdown + PDF output following PRISMA-adjacent conventions adapted for ML/stats survey papers.
allowed-tools: Read, Write, Edit, Bash, WebFetch
user-invocable: true
metadata:
    skill-author: chenlu-hung
    target-domain: machine-learning, statistics, operator-learning
---

# Literature Review (ML / Statistics)

## Trigger

`/literature-review-ml <topic>` or invoke when conducting systematic literature reviews / survey papers in ML or statistics.

## Overview

Conduct rigorous, survey-paper-grade literature reviews tailored to ML and statistics research. Search multiple academic sources via free APIs (arXiv, Semantic Scholar, OpenAlex), extract ML-specific metadata (architecture, dataset, metrics, code link, compute), assess reproducibility, synthesize thematically, verify citations, and produce both markdown and PDF outputs.

This skill is designed for **survey/review-paper rigor** — every paper goes through a documented PRISMA-adjacent flow, all citations are DOI/arXiv-ID verified, and reproducibility is explicitly assessed.

## When to Use This Skill

- Writing a survey/review paper for venues like *Foundations and Trends in ML*, *ACM Computing Surveys*, *Statistical Science*
- Thesis literature review chapter requiring systematic methodology
- Comprehensive related work for a research paper that needs full provenance
- Any review where PRISMA flow and citation verification are required

For lightweight ad-hoc related-work writing, use a less heavy approach instead.

## Core Workflow

The review proceeds in 8 phases. **Do not skip phases.** Track progress with TaskCreate.

---

### Phase 1: Scoping (PMDB Frame)

ML/stats reviews use the **PMDB frame** instead of clinical PICO:

- **P — Problem domain**: What task / problem setting? (e.g., "operator learning for parametric PDEs", "high-dimensional variable selection")
- **M — Method family scope**: Which families of approaches? (e.g., "neural operators (FNO, DeepONet, GNO)", "regularization-based methods (LASSO, SCAD, MCP)")
- **D — Data / benchmark scope**: Which datasets / benchmarks? (e.g., "Burgers, Darcy, Navier-Stokes from PDEBench", "simulated and UCI benchmarks")
- **B — Baselines and metrics**: What metrics / baselines define progress? (e.g., "relative L2 error vs FEM ground truth", "support recovery rate, FDR")

Write these out explicitly before searching. Save to `scope.md` in the review directory.

**Also define:**
- Time range (e.g., 2015–present for neural operators; 1996–present for sparse regression)
- Inclusion criteria (peer-reviewed + arXiv preprints with ≥X citations? workshop papers? thesis-only work?)
- Exclusion criteria (industry blog posts, retracted, superseded by later versions, etc.)
- Language (typically English)

---

### Phase 2: Multi-source Search

**Minimum 3 sources.** Run each in parallel where possible.

#### Source 1: arXiv (primary for ML preprints)

```bash
python scripts/search_arxiv.py "neural operator" \
    --categories cs.LG,stat.ML,math.NA \
    --year-start 2020 --year-end 2025 \
    --max-results 200 \
    --output sources/arxiv_neural_operator.json
```

arXiv categories cheat sheet (most relevant for this skill):
- `cs.LG` — Machine Learning (most ML papers)
- `stat.ML` — Stats-ML cross
- `cs.AI` — AI general
- `cs.CV` — Computer Vision
- `cs.CL` — NLP
- `math.ST` — Mathematical Statistics
- `math.NA` — Numerical Analysis (PDE solvers, operator learning)
- `math.PR` — Probability
- `physics.comp-ph` — Computational Physics (PINN, SciML)

See `references/search_strategies.md` for full category list and query syntax.

#### Source 2: Semantic Scholar (citation counts + venue resolution)

```bash
python scripts/search_semantic_scholar.py "neural operator parametric PDE" \
    --year-start 2020 --year-end 2025 \
    --min-citations 10 \
    --max-results 100 \
    --output sources/s2_neural_operator.json
```

Semantic Scholar gives:
- `citationCount`, `influentialCitationCount` (S2's quality-weighted metric)
- `venue` (resolved conference/journal name)
- `externalIds` (DOI, ArXiv, PubMed, MAG)
- `openAccessPdf` link

Use this to identify the most-cited / most-influential papers in the field.

#### Source 3: OpenAlex (institutional metadata + topic taxonomy)

```bash
python scripts/search_openalex.py "neural operator" \
    --year-start 2020 --year-end 2025 \
    --max-results 100 \
    --output sources/openalex_neural_operator.json
```

OpenAlex provides authoritative author disambiguation, institution affiliations, and a clean topic taxonomy. Free, no API key needed.

#### Optional Source 4: CrossRef (journal papers)

For statistics-heavy reviews where journal coverage matters:

```bash
python scripts/search_crossref.py "high dimensional variable selection" \
    --year-start 2000 --year-end 2025 \
    --output sources/crossref_varsel.json
```

#### Optional Source 5: PubMed (biostatistics + statistics journals)

For reviews touching biostatistics or statistical methodology published in journals
like *Biometrics*, *Biostatistics*, *Statistics in Medicine*, *JASA* (applications section),
or *Statistical Methods in Medical Research*. PubMed covers these comprehensively
and returns full abstracts even for paywalled articles.

```bash
python scripts/search_pubmed.py "variable selection penalized regression" \
    --year-start 2000 --year-end 2025 \
    --max-results 200 \
    --output sources/pubmed_varsel.json
```

PubMed supports field-tagged queries for precision:
- `[Title]` — search title only (reduces noise)
- `[MeSH Terms]` — Medical Subject Headings (controlled vocabulary)
- `[Journal]` — restrict to a specific journal
- `[Author]` — author name

Example: `"LASSO[Title] AND (statistics[MeSH] OR regression[MeSH])"`

**Limitation**: PubMed does not expose citation counts. After retrieval, enrich
citation data by matching on DOI via Semantic Scholar's `externalIds.PubMed` field.

#### Document the search

For each query, save the exact query string, date, source, and result count. This is required for survey papers.

```markdown
## Search Log
| Date       | Source           | Query                                          | Results |
|------------|------------------|------------------------------------------------|---------|
| 2026-05-15 | arXiv            | "neural operator" + cs.LG,stat.ML,math.NA       | 187     |
| 2026-05-15 | Semantic Scholar | "neural operator parametric PDE" + min_cit=10   | 84      |
| 2026-05-15 | OpenAlex         | "neural operator"                               | 92      |
```

---

### Phase 3: Screening + Deduplication

```bash
python scripts/aggregate.py sources/*.json \
    --deduplicate \
    --rank citations \
    --year-start 2020 \
    --output screened/all_papers.json \
    --format markdown > screened/all_papers.md
```

Deduplication priority: `arxiv_id` → `doi` → `title` (normalized).

**Three-stage screening:**

1. **Title screening** — Mark each paper INCLUDE / EXCLUDE / MAYBE based on title alone. Document reasons.
2. **Abstract screening** — For INCLUDE/MAYBE, read abstract, apply inclusion criteria.
3. **Full-text screening** — For survivors, fetch full text and assess deeply.

Track via PRISMA-style flow:

```
Identified (n=363) — arXiv: 187 | S2: 84 | OpenAlex: 92
    │
    ▼ Deduplication
After dedup (n=241)
    │
    ▼ Title screening
After title (n=78)
    │
    ▼ Abstract screening
After abstract (n=42)
    │
    ▼ Full-text screening
Included (n=31)
```

Save flow numbers to `prisma_flow.md` for inclusion in the final review.

---

### Phase 4: Data Extraction (ML/Stats Schema)

For each included paper, extract fields below into `extracted/{paper_slug}.yaml`. **Do not skip "compute" or "code" fields** — these are central to reproducibility in ML.

```yaml
# Bibliographic
title: "Fourier Neural Operator for Parametric Partial Differential Equations"
authors: ["Li, Z.", "Kovachki, N.", "Azizzadenesheli, K.", ...]
year: 2021
venue: ICLR
venue_tier: 1
arxiv_id: "2010.08895"
doi: ""
citation_count: 1842
influential_citations: 287

# ML-specific
problem_setting: "operator learning for parametric PDEs"
method_family: "neural operator (spectral)"
method_name: "FNO"
architecture: "Fourier layer + pointwise MLP; FFT-based global integral kernel"
key_contribution: "First spectral neural operator; resolution-invariant; outperforms baselines on Navier-Stokes by 10x"

# Empirical
datasets: ["Burgers (synthetic)", "Darcy flow", "Navier-Stokes (vorticity)"]
metrics: ["relative L2 error"]
baselines: ["U-Net", "DeepONet", "GNO", "FCN", "ResNet"]
sota_claim: true

# Reproducibility (CRITICAL — do not skip)
code_url: "https://github.com/zongyi-li/fourier_neural_operator"
code_license: "MIT"
pretrained_checkpoint: false
hyperparameters_reported: true
multiple_seeds: false  # papers should report ≥3
hardware_reported: "1x V100"
training_time_reported: true
statistical_test_reported: false

# Theoretical
theoretical_contributions: "universal approximation theorem for FNO"
proof_provided: true

# Notes
limitations_noted: "fixed input/output resolution at training; struggles with sharp discontinuities"
extensions_referenced: ["AFNO", "FFNO", "GINO", "U-FNO"]
```

A field template is available in `assets/extraction_template.yaml`.

---

### Phase 5: Quality Assessment

ML/stats reviews use a **reproducibility-focused quality framework** instead of clinical risk-of-bias tools.

For **each ML paper**, score on the NeurIPS/JMLR-inspired reproducibility checklist:

| Dimension                       | High (3)                 | Medium (2)         | Low (1)        | None (0)           |
|---------------------------------|--------------------------|--------------------|----------------|--------------------|
| Code availability               | Public + clean + tests   | Public, partial    | Available on request | Not available |
| Hyperparameter reporting        | Full + ablation          | Full               | Partial        | Missing            |
| Multiple seeds / error bars     | ≥5 seeds + CI            | 3-5 seeds          | 1-2 seeds      | None               |
| Compute disclosure              | Hardware + time + cost   | Hardware + time    | Hardware only  | None               |
| Statistical testing             | Significance + effect    | Effect size        | Mean only      | None               |
| Fair comparison                 | Same splits + protocol   | Same data          | Different      | Unclear            |

Total: 0–18. Flag papers scoring <6 as "low reproducibility — interpret claims with caution".

For **statistics papers**, use additionally:
- Are assumptions clearly stated?
- Are theorems' regularity conditions verifiable?
- Is simulation code provided?
- Are real-data analyses replicable?

---

### Phase 6: Thematic Synthesis (NOT paper-by-paper)

**Critical**: Organize Results by **method families / themes**, NOT by individual paper summaries. This is the single biggest pitfall in ML literature reviews.

For ML, common organizing axes:

1. **By method family** — e.g., "Spectral methods (FNO, AFNO, FFNO) | Graph-based (GNO, MGN) | Attention-based (Galerkin transformer, OFormer) | DeepONet variants"
2. **By problem regime** — e.g., "Forward problems | Inverse problems | Operator learning under distribution shift"
3. **By theoretical vs empirical contribution**
4. **By computational scaling regime** — e.g., "Methods for n<1k | Mid-scale | Large-scale foundation models"

For each theme:
- Synthesize across multiple papers (consensus, controversy, gaps)
- Compare results on **shared benchmarks** with **shared metrics** — create a benchmark table
- Note when comparisons are NOT fair (different splits, different problem setups)
- Identify methodological evolution (what improved when)

**Benchmark comparison table** (mandatory for ML reviews when applicable):

```markdown
| Method | Burgers (rel L2) | Darcy (rel L2) | NS (rel L2) | Params | Train (h) | Hardware |
|--------|------------------|----------------|-------------|--------|-----------|----------|
| FNO    | 1.6e-3           | 1.1e-2         | 1.3e-1      | 0.4M   | 0.4       | 1xV100   |
| ...    |                  |                |             |        |           |          |
```

Annotate the table with footnotes when reported numbers come from different sources / settings.

**Prose hygiene (avoid AI-tell writing).** Synthesis prose is where a review most often
reads as machine-generated. After drafting each thematic subsection, run the AI-tell pass
in `references/prose_hygiene.md` (or the `stop-slop` skill if installed). The worst
offenders in surveys: field-level false agency ("the literature reveals" → name the
papers), puffery adjectives ("seminal", "groundbreaking"), vague gap statements
("challenges remain" → name the specific gap), and monotone paper-by-paper sentence
cadence ("Smith et al. propose… Jones et al. propose…").

---

### Phase 7: Citation Verification

**Mandatory** before finalizing. All citations must resolve.

```bash
python scripts/verify_citations.py review_draft.md \
    --check-arxiv --check-doi \
    --output verification_report.json
```

The script:
- Extracts every `arxiv:XXXX.XXXXX` and `doi:10.XXXX/...` pattern
- Verifies each arXiv ID resolves and matches stated authors/year
- Verifies each DOI resolves via CrossRef and matches metadata
- Flags mismatches (wrong year, wrong authors, hallucinated papers)
- Outputs report listing PASS / WARN / FAIL per citation

Re-run until zero FAIL. WARN is acceptable but should be hand-reviewed (e.g., title differs slightly).

---

### Phase 8: PDF Generation

```bash
python scripts/generate_pdf.py review_draft.md \
    --citation-style nature \
    --output review.pdf
```

Citation styles available: `apa`, `nature`, `ieee`, `vancouver`, `acm`.

For ML survey papers, `nature` (superscript) or `acm` (numbered brackets) are most common. For statistics, `apa` (author-year) is more common.

**Quality checklist before submission:**
- [ ] PRISMA flow diagram included
- [ ] Search log fully documented (date, source, query, count)
- [ ] All papers have arxiv_id OR doi
- [ ] All citations verified (`verify_citations.py` clean)
- [ ] Reproducibility assessment for each paper
- [ ] At least one benchmark comparison table (if applicable)
- [ ] Results organized thematically, not study-by-study
- [ ] Prose passes the AI-tell check (`references/prose_hygiene.md`) — no field-level false agency, puffery, vague gaps, or paper-by-paper cadence
- [ ] Limitations of the review itself acknowledged
- [ ] Search end-date stated explicitly in methodology

---

## ML / Stats Venue Tiers

Use these to prioritize papers and assess venue quality. Full list in `references/ml_venues.md`.

### Machine Learning (broad)
- **Tier 1**: NeurIPS, ICML, ICLR, JMLR
- **Tier 2**: AISTATS, UAI, COLT, AAAI, IJCAI, TMLR
- **Tier 3 (subfield)**: CVPR/ICCV/ECCV (vision), ACL/EMNLP/NAACL (NLP), KDD/WWW (data mining), MICCAI (medical), L4DC (control)

### Statistics
- **Tier 1**: Annals of Statistics, JASA, Biometrika, JRSS-B
- **Tier 2**: Biometrics, AoAS, Statistica Sinica, JCGS, JMLR (theoretical)
- **Tier 3**: Statistical Science, Bayesian Analysis, JRSS-C, ElectronJ Stat

### Scientific Machine Learning / Operator Learning
- **Tier 1**: NeurIPS, ICML, ICLR + Nature Machine Intelligence, JCP, CMAME
- **Tier 2**: SIAM J. Sci. Comp., J. Mach. Learn. Sci., JMLR
- **Workshop venues**: AI4Science (NeurIPS), ML4PS, SciML workshops — cite but flag as workshop

**Workshop papers**: cite with explicit "[Workshop]" tag in venue field; assess separately. Many ML breakthroughs first appeared in workshops (e.g., word2vec at ICLR workshop).

---

## Citation Count Thresholds (ML/Stats Adjusted)

ML papers get cited faster than biomedical papers. Adjusted thresholds:

| Paper Age   | Noteworthy | Highly Influential | Landmark |
|-------------|------------|--------------------|----------|
| 0–1 year    | 30+        | 100+               | 300+     |
| 1–3 years   | 100+       | 300+               | 1000+    |
| 3–5 years   | 300+       | 1000+              | 3000+    |
| 5+ years    | 1000+      | 3000+              | 10000+   |

For statistics, divide thresholds by ~3 (stats citation velocity is lower).

Always prefer `influentialCitationCount` (Semantic Scholar's metric) over raw citation count — it filters out non-substantive citations.

---

## Best Practices

### Search
1. **Don't search ML literature with Google Scholar alone** — citation counts there include preprint duplicates
2. **Always include arXiv** — most ML work appears there first; many never get formal publication
3. **Track arXiv version** — papers revise substantially; cite the version you actually read (`arXiv:2010.08895v3`)
4. **Use S2's `influentialCitationCount`** to surface real influence vs polite-cite-everything papers
5. **Don't filter out workshop papers categorically** — some seminal work is workshop-only

### Synthesis
1. **Thematic, not paper-by-paper** — single biggest pitfall
2. **Benchmark tables** when methods address same problem with same metrics
3. **Flag unfair comparisons explicitly** — different splits, different compute budgets
4. **Distinguish theoretical from empirical contributions** — many ML papers conflate these
5. **Track method genealogy** — who extended whom (e.g., FNO → AFNO → FFNO → GINO)
6. **No AI-tell prose** — run `references/prose_hygiene.md`: attribute claims to named papers instead of "the literature shows", cut puffery adjectives, name specific gaps

### Reproducibility
1. **Report code availability per paper** — central to ML; missing in most biomed reviews
2. **Note multi-seed / error bars** — many ML papers report single-run; treat with skepticism
3. **Note compute disclosure** — large-compute papers are hard to verify
4. **Flag claims requiring access to undisclosed resources** (datasets, checkpoints)

---

## Common Pitfalls

1. **Citing the arXiv version when a journal version exists** — always check if a paper was later published
2. **Using citation count alone to gauge importance** — `influentialCitationCount` is better, but reading abstract+intro is best
3. **Treating workshop papers as low-quality** — many are highly influential (e.g., AlexNet was NIPS, but word2vec was workshop)
4. **Comparing methods across different problem setups** — always check evaluation protocol
5. **Missing the latest preprints** — set search end-date close to submission
6. **Ignoring software/library papers** — JAX, PyTorch, scikit-learn papers are highly cited and often relevant
7. **Hallucinating citations** — LLMs invent plausible-sounding papers; verify every DOI/arXiv ID
8. **Skipping reproducibility assessment** — accepting claims without checking if anyone can verify them
9. **AI-tell prose** — "the literature reveals", "seminal/groundbreaking", "challenges remain", and Author-et-al-by-Author-et-al cadence make a review read as machine-written; run `references/prose_hygiene.md`

---

## Example: Operator Learning for PDEs Review

Full example workflow:

```bash
# 1. Create workspace
mkdir -p ~/reviews/operator_learning/{sources,screened,extracted,figures}
cd ~/reviews/operator_learning

# 2. Define scope (write scope.md by hand using PMDB frame)

# 3. Search
python ~/.claude/skills/literature-review-ml/scripts/search_arxiv.py \
    "neural operator OR DeepONet OR FNO" \
    --categories cs.LG,stat.ML,math.NA \
    --year-start 2019 --year-end 2026 \
    --max-results 300 \
    --output sources/arxiv.json

python ~/.claude/skills/literature-review-ml/scripts/search_semantic_scholar.py \
    "neural operator parametric PDE" \
    --year-start 2019 --year-end 2026 \
    --min-citations 5 \
    --max-results 200 \
    --output sources/s2.json

python ~/.claude/skills/literature-review-ml/scripts/search_openalex.py \
    "neural operator" \
    --year-start 2019 --year-end 2026 \
    --max-results 200 \
    --output sources/openalex.json

# 4. Aggregate and screen
python ~/.claude/skills/literature-review-ml/scripts/aggregate.py \
    sources/arxiv.json sources/s2.json sources/openalex.json \
    --deduplicate --rank influential_citations \
    --output screened/candidates.json \
    --format markdown > screened/candidates.md

# 5. Manual screening (title → abstract → full-text)
#    Mark each paper INCLUDE/EXCLUDE/MAYBE in candidates.md

# 6. Extract data per included paper (use assets/extraction_template.yaml)

# 7. Write review using assets/review_template.md as starting point

# 8. Verify citations
python ~/.claude/skills/literature-review-ml/scripts/verify_citations.py \
    review.md --check-arxiv --check-doi

# 9. Generate PDF
python ~/.claude/skills/literature-review-ml/scripts/generate_pdf.py \
    review.md --citation-style nature --output review.pdf
```

---

## Bundled Resources

**Scripts** (in `scripts/`):
- `search_arxiv.py` — arXiv API search
- `search_semantic_scholar.py` — Semantic Scholar Graph API
- `search_openalex.py` — OpenAlex API
- `search_crossref.py` — CrossRef (journals)
- `aggregate.py` — dedup, rank, filter, format
- `verify_citations.py` — arXiv ID + DOI verification
- `generate_pdf.py` — pandoc wrapper

**References** (in `references/`):
- `ml_venues.md` — venue tier list (ML + stats + SciML)
- `search_strategies.md` — arXiv categories, S2 query tips, OpenAlex filters
- `citation_styles.md` — APA / Nature / IEEE / ACM / Vancouver
- `prose_hygiene.md` — AI-tell checklist for survey prose (stop-slop, academic-adapted)

**Assets** (in `assets/`):
- `review_template.md` — full review skeleton with PMDB, PRISMA flow, etc.
- `extraction_template.yaml` — per-paper extraction schema

---

## Dependencies

### Python (standard)
```bash
pip install requests pyyaml
```

### For PDF output
```bash
# macOS
brew install pandoc
brew install --cask mactex  # for xelatex

# Linux
apt-get install pandoc texlive-xetex
```

Check with:
```bash
python scripts/generate_pdf.py --check-deps
```

---

## Summary

This skill provides:
1. **PMDB scoping frame** suited to ML/stats (replaces PICO)
2. **Free, no-key API search** across arXiv, Semantic Scholar, OpenAlex
3. **ML-specific extraction schema** capturing code, compute, seeds, baselines
4. **Reproducibility-focused quality assessment** (NeurIPS/JMLR-style)
5. **Thematic synthesis with benchmark tables** as the synthesis output
6. **Citation verification** for both arXiv IDs and DOIs
7. **Survey-paper-grade PDF output** via pandoc
8. **AI-tell-free prose** via an academic-adapted `stop-slop` pass on every synthesis paragraph
