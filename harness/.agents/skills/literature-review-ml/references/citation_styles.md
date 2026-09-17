# Citation Styles Reference

Pick one style and use it consistently. For ML survey papers, **Nature** (superscript) or **ACM** (numbered brackets) are most common. For statistics, **APA** (author-year) is standard.

## APA (7th Edition) — Author-year, most stats

**In-text**: `(Li et al., 2021)` or `Li et al. (2021)`

**Reference**:
```
Li, Z., Kovachki, N., Azizzadenesheli, K., Liu, B., Bhattacharya, K., Stuart, A., & Anandkumar, A. (2021). Fourier neural operator for parametric partial differential equations. In *Proceedings of the 9th International Conference on Learning Representations* (ICLR 2021). https://arxiv.org/abs/2010.08895
```

Use when: writing for statistics journals, biostatistics, applied stats, or interdisciplinary audiences.

---

## Nature — Superscript numbers, ML common

**In-text**: `...Fourier neural operators¹,² have shown promise...`

**Reference list (numbered, in order of first citation)**:
```
1. Li, Z. et al. Fourier neural operator for parametric partial differential equations. In *ICLR 2021* (2021).
2. Lu, L., Jin, P. & Karniadakis, G. E. DeepONet: Learning nonlinear operators based on the universal approximation theorem of operators. *Nat. Mach. Intell.* **3**, 218–229 (2021).
```

Use when: writing for Nature family, *Nature Machine Intelligence*, *Nature Computational Science*, general scientific audiences.

---

## IEEE — Bracketed numbers, engineering / vision

**In-text**: `As shown in [1] and [2], FNO outperforms...`

**Reference**:
```
[1] Z. Li et al., "Fourier neural operator for parametric partial differential equations," in *Proc. ICLR*, 2021. [Online]. Available: https://arxiv.org/abs/2010.08895
[2] L. Lu, P. Jin, and G. E. Karniadakis, "DeepONet: Learning nonlinear operators based on the universal approximation theorem of operators," *Nat. Mach. Intell.*, vol. 3, pp. 218–229, 2021.
```

Use when: writing for IEEE conferences/journals, computer vision (CVPR/ICCV/ECCV), engineering.

---

## ACM — Numbered, mostly NeurIPS-adjacent

**In-text**: `Neural operators [12, 24] have...`

**Reference**:
```
[12] Zongyi Li, Nikola Kovachki, Kamyar Azizzadenesheli, Burigede Liu, Kaushik Bhattacharya, Andrew Stuart, and Anima Anandkumar. 2021. Fourier neural operator for parametric partial differential equations. In *International Conference on Learning Representations*.
[24] Lu Lu, Pengzhan Jin, and George Em Karniadakis. 2021. DeepONet: Learning nonlinear operators based on the universal approximation theorem of operators. *Nature Machine Intelligence* 3, 3, 218–229.
```

Use when: writing for ACM venues (KDD, SIGIR, CHI), JMLR (similar style), NeurIPS proceedings (similar).

---

## Vancouver — Superscript or bracketed, medical/biomedical

**In-text**: `Studies have shown¹,² that...`

**Reference**:
```
1. Li Z, Kovachki N, Azizzadenesheli K, et al. Fourier neural operator for parametric partial differential equations. In: International Conference on Learning Representations; 2021.
2. Lu L, Jin P, Karniadakis GE. DeepONet: Learning nonlinear operators based on the universal approximation theorem of operators. Nat Mach Intell. 2021;3:218-29.
```

Use when: medical / biomedical journals.

---

## Style decision flowchart

```
Writing for…
├── Statistics journal (JASA, AoS, etc.) ──────────→ APA
├── Biostatistics journal ─────────────────────────→ APA or Vancouver
├── Nature / Science family ───────────────────────→ Nature
├── NeurIPS / ICML / ICLR / JMLR ──────────────────→ ACM-style or use the venue's template
├── IEEE conference / journal ─────────────────────→ IEEE
├── ACM conference / journal ──────────────────────→ ACM
├── Medical / clinical ────────────────────────────→ Vancouver
└── Thesis ────────────────────────────────────────→ Match advisor's preference; APA is safe default
```

---

## Always include

For every citation, ensure you have:
1. All authors (or "et al." after first 3–6 depending on style)
2. Year
3. Title
4. Venue (full journal name or conference proceedings name)
5. Volume / issue / page numbers (for journals)
6. DOI **or** arXiv ID **or** stable URL

**Avoid**:
- "et al." with only 2 authors (most styles require ≥3 to abbreviate)
- Inconsistent author name formatting (Last, F. vs F. Last)
- Mixing styles within one document
- Citing only the arXiv version when a journal/conference version exists — cite the published version primarily

---

## arXiv-only papers

When citing a paper that exists only as preprint:

**APA**: `Smith, J. (2024). Title of paper. *arXiv*. https://arxiv.org/abs/2401.12345`

**Nature**: `Smith, J. Title of paper. Preprint at https://arxiv.org/abs/2401.12345 (2024).`

**IEEE**: `J. Smith, "Title of paper," arXiv:2401.12345, 2024.`

Always include the arXiv ID. Always include the year.
