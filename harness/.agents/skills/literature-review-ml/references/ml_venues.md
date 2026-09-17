# ML / Statistics Venue Tier Reference

This list classifies venues by typical reputation in the relevant subfield. Tiers shift over time, so use this as a starting point; check `influentialCitationCount` from Semantic Scholar for the actual influence of each paper.

## Machine Learning (general / methodological)

### Tier 1 — Top general ML
| Venue   | Type       | Notes                                                   |
|---------|------------|---------------------------------------------------------|
| NeurIPS | Conference | Largest general ML venue; rigorous review               |
| ICML    | Conference | High theoretical bar                                    |
| ICLR    | Conference | Representation learning + deep learning; open review    |
| JMLR    | Journal    | Highest-bar ML journal; theoretical work                |

### Tier 2 — Strong general ML
| Venue   | Type       | Notes                                                   |
|---------|------------|---------------------------------------------------------|
| AISTATS | Conference | Statistics-flavored ML                                  |
| UAI     | Conference | Probabilistic ML, causality                             |
| COLT    | Conference | Learning theory                                         |
| TMLR    | Journal    | Open-access ML journal (no novelty bar)                 |
| AAAI    | Conference | Broad AI                                                |
| IJCAI   | Conference | Broad AI                                                |

### Tier 3 — Strong subfield venues
| Venue        | Subfield                |
|--------------|-------------------------|
| CVPR/ICCV/ECCV | Computer vision       |
| ACL/EMNLP/NAACL | NLP                  |
| KDD          | Data mining             |
| WWW          | Web / IR / data mining  |
| RecSys       | Recommender systems     |
| L4DC         | ML + control            |
| MICCAI       | Medical image analysis  |
| ISMB/RECOMB  | Computational biology   |
| RSS / CoRL   | Robotics + ML           |

### Workshops (NeurIPS / ICML / ICLR)
Tier varies. Many influential papers first appeared at workshops (word2vec, FNO precursors, etc.). When citing, append `[Workshop]` to the venue and treat as preprint-grade evidence until full paper is out.

---

## Statistics

### Tier 1 — Top methodological statistics
| Venue                                  | Notes                                |
|----------------------------------------|--------------------------------------|
| Annals of Statistics (AoS)             | Theoretical statistics flagship      |
| Journal of the American Statistical Association (JASA) | Methodology + applications |
| Biometrika                             | Methodology, classic                 |
| Journal of the Royal Statistical Society B (JRSS-B) | Methodology       |

### Tier 2 — Strong statistics
| Venue                                  | Notes                                |
|----------------------------------------|--------------------------------------|
| Biometrics                             | Biostatistics methodology            |
| Annals of Applied Statistics (AoAS)    | Applied methodology                  |
| Statistica Sinica                      | Methodology                          |
| Journal of Computational and Graphical Statistics (JCGS) | Computational stats |
| Journal of the Royal Statistical Society C (JRSS-C)  | Applied stats        |
| Bayesian Analysis                      | Bayesian methodology                 |
| Statistics and Computing               | Methodology + computation            |

### Tier 3 — Specialized / general
| Venue                          | Notes                                |
|--------------------------------|--------------------------------------|
| Statistical Science            | Review articles + methodology        |
| Electronic Journal of Statistics | Open-access theory + methodology  |
| Annals of Applied Probability  | Applied probability                  |
| Probability Theory and Related Fields | Theoretical probability       |

---

## Scientific Machine Learning / Operator Learning / Computational Science

### Tier 1
| Venue                                  | Notes                                |
|----------------------------------------|--------------------------------------|
| Nature Machine Intelligence            | Cross-disciplinary AI for science    |
| Nature Computational Science           |                                      |
| Journal of Computational Physics (JCP) | Numerical methods + SciML            |
| Computer Methods in Applied Mechanics and Engineering (CMAME) | Engineering computational methods |
| SIAM J. Sci. Computing (SISC)          | Scientific computing                 |
| NeurIPS / ICML / ICLR                  | Methodological ML side               |

### Tier 2
| Venue                                            | Notes                            |
|--------------------------------------------------|----------------------------------|
| J. Mach. Learn. for Sci.                         | Open-access SciML                |
| SIAM J. Numerical Analysis                       | Numerical analysis theory        |
| Journal of Scientific Computing                  | Broader SciComp                  |
| Foundations of Data Science                      | Theoretical data science         |
| Communications of the AMS                        | Mathematical methods             |

### Workshop / Specialized
| Venue                                  | Notes                                |
|----------------------------------------|--------------------------------------|
| AI4Science (NeurIPS workshop)          | SciML cutting-edge                   |
| ML4PS (NeurIPS workshop)               | ML for physical sciences             |
| LoG conference                         | Graph learning                       |
| ICLR SimDL                             | Simulation + DL                      |

---

## Industry / Engineering Venues (treat carefully)

| Venue          | Notes                                                          |
|----------------|----------------------------------------------------------------|
| arXiv-only     | Many ML breakthroughs are arXiv-first; verify citation count   |
| Tech reports   | Google / OpenAI / DeepMind / Meta reports — cite the URL       |
| Workshop       | Cite with `[Workshop]` tag                                     |
| Thesis         | PhD theses are citable; include institution                    |

---

## How to use these tiers in a review

1. **Reporting**: For each cited paper, record its venue and tier in the extraction template (`assets/extraction_template.yaml`).
2. **Filtering**: When dealing with a huge candidate pool, consider including only Tier 1+2 venues + highly-cited preprints (e.g., 50+ citations within 2 years).
3. **Reporting bias**: When the review skews heavily toward Tier 1 venues, note this in limitations — important work may live in workshops or specialized venues.
4. **Workshop papers**: Don't exclude them. Many influential ML breakthroughs were workshop-only when first published (word2vec, AlphaGo Zero technical details, several foundation model papers).
