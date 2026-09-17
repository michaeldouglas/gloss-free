---
title: "[Survey Title]"
author:
  - "[Author 1]^1^"
  - "[Author 2]^2^"
date: "YYYY-MM-DD"
abstract: |
  [150–250 words. State (1) the scope/motivation, (2) what was searched and how,
  (3) main findings organized thematically, (4) gaps and future directions.]
keywords: [keyword1, keyword2, keyword3, keyword4, keyword5]
---

# Abstract

[See YAML above. Repeat here for journals that need it inline.]

---

# 1. Introduction

## 1.1 Motivation

[Why this review now? What scientific or methodological question motivates the synthesis? What changed recently that makes a review worthwhile?]

## 1.2 Scope and contribution

This review addresses the following questions:

1. [Q1: e.g., What method families exist for X?]
2. [Q2: e.g., How do they compare on benchmark Y?]
3. [Q3: e.g., What are the open theoretical/empirical gaps?]

Our contribution: [(a) a structured taxonomy, (b) a benchmark comparison, (c) an identification of N gaps, etc.]

## 1.3 Related surveys

[Briefly review prior surveys covering overlapping ground. State how this survey is distinct in scope, time period, or perspective. Cite each prior survey explicitly.]

---

# 2. Methodology

## 2.1 Research questions (PMDB frame)

- **P — Problem domain**: [e.g., operator learning for parametric PDEs in 2D/3D]
- **M — Method family scope**: [e.g., neural operators including FNO, DeepONet, GNO, Galerkin transformer, MGN]
- **D — Data / benchmark scope**: [e.g., Burgers, Darcy, NS, plus PDEBench tasks; excludes Lagrangian particle methods]
- **B — Baselines and metrics**: [e.g., relative L2 error vs FEM ground truth; comparison against U-Net baselines]

## 2.2 Inclusion and exclusion criteria

**Inclusion:**
- [e.g., Published 2019-01 to 2026-05]
- [e.g., Peer-reviewed papers OR arXiv preprints with ≥10 citations]
- [e.g., Methods evaluated on at least one parametric PDE benchmark]
- [e.g., English language]

**Exclusion:**
- [e.g., Workshop papers without subsequent peer review AND <5 citations]
- [e.g., Pure CFD/FEM papers without learning component]
- [e.g., Industry blog posts, social media discussions]
- [e.g., Superseded by later versions of same work]

## 2.3 Search strategy

| Source             | Date searched | Query                                                  | Initial results |
|--------------------|---------------|--------------------------------------------------------|-----------------|
| arXiv              | 2026-05-15    | `(cs.LG OR stat.ML OR math.NA) AND "neural operator"`   | 187             |
| Semantic Scholar   | 2026-05-15    | `"neural operator parametric PDE"` min-cit=10           | 84              |
| OpenAlex           | 2026-05-15    | `"neural operator"` type:article                        | 92              |
| **Total identified** | | | **363** |

Full search scripts and JSON outputs are available in the supplementary materials.

## 2.4 Screening (PRISMA-style flow)

```
Identified (n=363)
    │  arXiv: 187 | S2: 84 | OpenAlex: 92
    │
    ▼ Deduplication (by arxiv_id, DOI, normalized title)
After dedup (n=241)
    │
    ▼ Title screening (against inclusion criteria)
After title (n=78) — excluded 163: out of scope (98), wrong type (32), superseded (12), unclear (21)
    │
    ▼ Abstract screening
After abstract (n=42) — excluded 36: weak relevance (18), no method contribution (10), no eval (8)
    │
    ▼ Full-text screening
Included in review (n=31) — excluded 11: full text unavailable (3), failed quality (4), duplicate work (4)
```

Reasons for exclusion at each stage are tabulated in Appendix A.

## 2.5 Data extraction

For each included paper we extracted the fields defined in our extraction template (see Appendix B), covering:

- Bibliographic metadata
- Method family and architecture
- Empirical evaluation (datasets, metrics, baselines)
- Reproducibility indicators (code, seeds, hardware, statistical tests)
- Theoretical contributions

## 2.6 Quality assessment

Each paper was scored on a 6-dimensional reproducibility scale (0–18 total) covering code availability, hyperparameter reporting, seed/error-bar reporting, compute disclosure, statistical testing, and fair-comparison practices. Papers scoring <6 are flagged in the synthesis as "low reproducibility — interpret claims with caution".

Venue tier was recorded but used as descriptive metadata rather than an inclusion filter, to avoid systematic exclusion of work in newer or specialized venues.

## 2.7 Synthesis approach

We organized findings thematically by **method family** (Section 3) and by **problem regime** (Section 4) rather than producing per-paper summaries. Where ≥3 papers reported results on a shared benchmark with matched protocol, we produced a comparison table (Section 5).

## 2.8 Limitations of this review

- [e.g., Cutoff at 2026-05; field moves fast]
- [e.g., English-language only]
- [e.g., No quantitative meta-analysis due to heterogeneous metrics]
- [e.g., Single reviewer for screening (no dual review)]
- [e.g., Bias toward methods released with code]

---

# 3. Method family taxonomy

[Organize ~3–6 themes. For each, synthesize across multiple papers. Avoid per-paper summaries.]

[Prose: run `references/prose_hygiene.md` on every paragraph — attribute claims to named papers (not "the literature shows"), cut puffery ("seminal", "groundbreaking"), name specific gaps (not "challenges remain"), and break the "Author et al. propose…" cadence.]

## 3.1 [Family 1: e.g., Spectral methods]

[Conceptual description of the family. Key foundational paper(s). Evolution. Strengths and limitations as a family.]

The spectral approach was introduced by [Li et al. 2021, arXiv:2010.08895] with the Fourier Neural Operator (FNO), which... Subsequent work extended this in three directions: [Direction A] (papers X, Y, Z), [Direction B] (papers W, V), and [Direction C] (paper U). The consensus is that spectral approaches excel on periodic domains but struggle with...

## 3.2 [Family 2]

[...]

## 3.3 [Family 3]

[...]

---

# 4. Problem regimes

[Cross-cutting analysis by problem type or data regime.]

## 4.1 [Regime A: e.g., Forward problems]

## 4.2 [Regime B: e.g., Inverse problems]

## 4.3 [Regime C: e.g., Out-of-distribution generalization]

---

# 5. Benchmark comparison

**Caveats**: Numbers below are taken from the cited papers' reported results. Comparisons across papers should be interpreted with care because of differing data splits, training budgets, and evaluation protocols. We note known protocol differences in footnotes.

| Method | Burgers (rel L2) | Darcy (rel L2) | NS-2D (rel L2) | Params | Train | Hardware | Source              |
|--------|------------------|----------------|----------------|--------|-------|----------|---------------------|
| FNO    | 1.6e-3           | 1.1e-2         | 1.3e-1         | 0.4M   | 0.4h  | 1xV100   | Li et al. 2021      |
| ...    | ...              | ...            | ...            | ...    | ...   | ...      | ...                 |

[Footnotes describing protocol differences]

---

# 6. Reproducibility landscape

[Summary of reproducibility scores across included papers. Identify systemic gaps (e.g., "Only 38% of included papers report >1 seed").]

| Dimension                 | Mean score (0–3) | % with full score | % with zero |
|---------------------------|------------------|-------------------|-------------|
| Code availability         | 2.1              | 45%               | 13%         |
| Hyperparameter reporting  | 2.4              | 58%               | 3%          |
| Multiple seeds            | 1.2              | 16%               | 35%         |
| Compute disclosure        | 1.8              | 32%               | 19%         |
| Statistical testing       | 0.6              | 6%                | 65%         |
| Fair comparison           | 2.0              | 35%               | 6%          |

---

# 7. Discussion

## 7.1 Consensus findings

[What is settled across the literature?]

## 7.2 Open controversies

[Where do papers disagree?]

## 7.3 Research gaps

[What questions are inadequately answered? Be specific.]

1. [Gap 1: e.g., no benchmark on 3D non-periodic domains]
2. [Gap 2: e.g., limited theoretical analysis of FNO variants]
3. [Gap 3: e.g., reproducibility for industrial-scale applications]

## 7.4 Future directions

[Specific concrete suggestions, not generic platitudes.]

---

# 8. Conclusion

[3–5 paragraphs. Restate the question, summarize the main findings by theme, highlight the most important gaps, and close with a forward-looking statement.]

---

# Acknowledgments

[Funding sources, computing acknowledgments, helpful discussions.]

---

# References

[Reference list. Use chosen citation style (APA / Nature / IEEE / ACM / Vancouver) consistently.]

---

# Appendices

## Appendix A: Excluded papers and reasons

[Optional table listing excluded papers at full-text stage and reason for exclusion. Required for PRISMA-compliant reviews.]

## Appendix B: Extraction template

[Reproduce or reference `assets/extraction_template.yaml`]

## Appendix C: Search queries (full text)

[The exact queries run, for reproducibility.]

## Appendix D: Reproducibility scoring details

[The full 6-dimensional scoring rubric and per-paper scores.]
