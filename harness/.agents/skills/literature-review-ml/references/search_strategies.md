# Search Strategies for ML / Statistics Literature

## arXiv

### Query syntax
- `all:term` — search in title, abstract, comments, authors
- `ti:term` — title only
- `abs:term` — abstract only
- `au:lastname` — author
- `cat:cs.LG` — primary category
- Boolean: `AND`, `OR`, `ANDNOT`
- Phrase: `"single cell"` with double quotes
- Group: `(cat:cs.LG OR cat:stat.ML) AND ti:operator`

### Relevant categories for ML / stats

**Machine learning core**
| Category    | Description                              |
|-------------|------------------------------------------|
| cs.LG       | Machine Learning (most ML papers)        |
| stat.ML     | Statistics — Machine Learning            |
| cs.AI       | Artificial Intelligence                  |
| cs.NE       | Neural and Evolutionary Computing        |

**Subfields**
| Category    | Description                              |
|-------------|------------------------------------------|
| cs.CV       | Computer Vision                          |
| cs.CL       | Computation and Language (NLP)           |
| cs.IR       | Information Retrieval                    |
| cs.RO       | Robotics                                 |
| cs.CR       | Cryptography (incl. ML privacy)          |
| cs.GT       | Game Theory (incl. multi-agent RL)       |
| cs.MA       | Multi-Agent Systems                      |

**Statistics**
| Category    | Description                              |
|-------------|------------------------------------------|
| stat.ML     | Statistics—Machine Learning              |
| stat.ME     | Methodology                              |
| stat.TH    | Theoretical Statistics                   |
| stat.AP     | Applications                             |
| stat.CO     | Computation                              |
| math.ST     | Mathematical Statistics                  |
| math.PR     | Probability                              |

**Scientific ML / numerics**
| Category          | Description                              |
|-------------------|------------------------------------------|
| math.NA           | Numerical Analysis                       |
| math.OC           | Optimization and Control                 |
| physics.comp-ph   | Computational Physics                    |
| physics.flu-dyn   | Fluid Dynamics                           |
| q-bio.QM          | Quantitative Methods                     |

### Sorting
arXiv API supports `sortBy=submittedDate` (newest first), `sortBy=lastUpdatedDate`, `sortBy=relevance`. Default in our search script is submittedDate descending.

### Rate limit
arXiv asks for ≥3 seconds between API requests. The search script enforces this.

### Citing arXiv papers
- Use `arXiv:2010.08895` format
- Include version (`v3`) if it matters
- If the paper was later published in a journal/conference, cite the published version primarily and note "preprint available at arXiv:..."

---

## Semantic Scholar

### Key endpoints
- Paper search: `https://api.semanticscholar.org/graph/v1/paper/search`
- Paper detail: `https://api.semanticscholar.org/graph/v1/paper/{id}`
- Recommendations: `https://api.semanticscholar.org/recommendations/v1/papers/forpaper/{id}`

### Useful filters in our wrapper
- `--year-start`, `--year-end` — date range
- `--min-citations N` — only papers with ≥N citations
- S2 supports `fieldsOfStudy` (e.g., "Computer Science", "Mathematics", "Engineering")

### `influentialCitationCount` vs `citationCount`
- `citationCount` — raw inbound citation count (includes "X is a related approach" type cites)
- `influentialCitationCount` — S2's filtered metric using ML to detect meaningful methodological influence; usually 5–15% of raw count

**Prefer `influentialCitationCount`** when ranking by impact. Raw citations inflate easily with self-citation or boilerplate references.

### Rate limit (no key)
S2 throttles unauthenticated requests aggressively. The search script sleeps ≥1s between requests and retries with exponential backoff on 429. For large surveys, consider getting a free API key at https://www.semanticscholar.org/product/api.

---

## OpenAlex

### Strengths
- Free, no key required
- Best author/institution disambiguation
- Clean "primary_topic" taxonomy
- Includes open-access PDF URLs
- 250M+ works indexed

### Filters
The search script supports year filtering and restricts to `type:article` by default. OpenAlex allows much richer filters:
- `concepts.id:C2779343474` — by concept ID
- `authorships.author.id:A1234567890`
- `host_venue.id:V12345`
- `cited_by_count:>100`

Refer to https://docs.openalex.org/api-entities/works/filter-works for full list.

### Polite pool
Add `--mailto your@email.com` to the search script. OpenAlex routes polite-pool requests faster and is more lenient with rate limits.

---

## CrossRef

### When to use
- Statistics journals (most ML preprints are on arXiv, but stats journals aren't)
- Verifying a paper was actually published in a journal (not just arXiv)
- Old papers (pre-arXiv-era)

### Ranking
Use `sort=is-referenced-by-count, order=desc` (script default) to surface highly-cited journal articles.

---

## Combining sources: recommended workflow

For most ML reviews, the right order is:

1. **arXiv (broad scoping)** — get a wide net of preprints in your method area
2. **Semantic Scholar (filter by impact)** — re-query with citation thresholds; surfaces published versions and influence rankings
3. **OpenAlex (institutional + topic verification)** — cross-check with topic taxonomy and add any missing journal papers
4. **CrossRef (only if needed)** — for stats-heavy reviews or older work

Then `aggregate.py` with `--deduplicate` merges everything by arxiv_id → DOI → title.

### Citation chaining

After initial screening, expand via:
- **Forward citations**: for each highly-cited included paper, look up its citers on Semantic Scholar:
  `https://api.semanticscholar.org/graph/v1/paper/{id}/citations`
- **Backward citations**: read each included paper's reference list and add anything that appears in ≥2 included papers' references but is not yet included

This is how you find seminal precursors and active follow-ups.

---

## Domain-specific search tips

### Operator learning / SciML
Useful query terms:
- `"neural operator"`, `"DeepONet"`, `"FNO"`, `"Fourier neural operator"`
- `"physics-informed neural network"`, `"PINN"`
- `"PDE surrogate"`, `"operator learning"`
- arXiv categories: `cs.LG`, `stat.ML`, `math.NA`, `physics.comp-ph`

Key venues: NeurIPS, ICML, ICLR, JCP, CMAME, SISC, Nature Machine Intelligence.

### High-dimensional statistics
Useful query terms:
- `"variable selection"`, `"sparse regression"`, `"LASSO"`, `"high dimensional"`
- `"oracle property"`, `"minimax"`, `"compressed sensing"`

Key venues: Annals of Statistics, JASA, Biometrika, JRSS-B, JMLR.

### Causal inference
Useful query terms:
- `"causal inference"`, `"average treatment effect"`, `"instrumental variable"`
- `"propensity score"`, `"doubly robust"`, `"causal forest"`

Key venues: JASA, AoS, Biometrika, JMLR, NeurIPS (Causal Learning workshops), AAAI.

### Bayesian methods
Useful query terms:
- `"variational inference"`, `"normalizing flow"`, `"MCMC"`, `"posterior approximation"`
- `"Bayesian neural network"`, `"uncertainty quantification"`

Key venues: Bayesian Analysis, JMLR, ICML, NeurIPS, AISTATS.

### Optimization for ML
Useful query terms:
- `"non-convex optimization"`, `"stochastic gradient"`, `"adaptive methods"`
- `"convergence rate"`, `"saddle point"`

Key venues: COLT, ICML, NeurIPS, SIAM J. Optimization, Math. Programming.
