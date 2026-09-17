# Prose Hygiene (no AI tells)

Run on **every prose paragraph you write** for the review — synthesis sections,
abstract, intro, discussion — before saving. A survey that reads as machine-generated
loses reviewer trust even when the underlying scholarship is sound. This is cheap and
mechanical.

**Engine vs. overlay.** If the `stop-slop` skill is available, invoke it on the prose
first — it is the general AI-tell engine. This file is the **survey/academic overlay**:
it (a) carries the core checks so the pass works when `stop-slop` is absent, (b) adds
the tells specific to literature reviews, and (c) lists the `stop-slop` rules to
**relax** for academic register (§E). Where they conflict, §E wins — `stop-slop` is
tuned for blog/essay prose, not survey papers.

---

## A. Phrase-level cuts

- **Hedge filler**: "it is worth noting (that)", "it should be noted", "importantly",
  "notably", "interestingly", "arguably". Delete, or state the claim itself.
- **Throat-clearing openers**: "In this section, we…", "It is important to understand…",
  "To begin with…". Start with the content.
- **AI-tell vocabulary**: "delve", "crucial", "pivotal", "leverage" (verb), "rich
  tapestry", "showcase", "underscore", "realm", "harness", "intricate", "seamless",
  "holistic". Use plain words.
- **Survey puffery — empty evaluative adjectives**: "seminal", "groundbreaking",
  "pioneering", "powerful", "promising", "remarkable", "compelling", "elegant". They
  assert importance without showing it. Replace with the specific contribution and its Δ:
  - ✗ "Li et al. proposed the seminal FNO, a groundbreaking approach."
  - ✓ "Li et al. (2021) introduced FNO, the first neural operator to learn in the
    spectral domain, cutting Navier-Stokes error ~10× over U-Net baselines."
- **Empty intensifiers**: "very", "highly", "extremely", "significantly" (unless
  reporting a statistical test — then give it), "substantially" (give the number).
- **Unscoped superlatives**: no "state-of-the-art / first / best" without scope
  (SOTA *on which benchmark, as of when?*).

## B. Structural tells (the strongest "AI smell" in surveys)

- **Field-level false agency** (a survey's #1 tell — an abstraction does a human verb so
  no one has to name the source): "the literature reveals", "research has shown", "the
  field has converged on", "the data suggests", "studies demonstrate", "the evidence
  points to". Name who: "Li et al. (2021) and Lu et al. (2021) independently show…",
  "Three groups report…". Narrative attribution is the antidote — and it strengthens a
  survey.
  - ✗ "The literature reveals a shift toward attention-based operators."
  - ✓ "Since 2022, Cao (2021) and Li et al. (2023) have moved to attention-based
    operators, citing FNO's fixed-resolution limitation."
- **Binary contrast / telegraphed reversal**: "early methods focused not on X but on Y",
  "the bottleneck is not X; it is Y", "not just X, but also Y". State the point directly.
- **Vague gap statements** (epidemic in AI-written related work): "However, challenges
  remain", "this remains an open problem", "more work is needed", "gaps persist". Name
  the specific gap and who would care:
  - ✗ "Despite progress, significant challenges remain."
  - ✓ "No method in Table 3 reports multi-seed variance, so the ranking among the top
    three is statistically unresolved."
- **Negative listing** ("Not an X. Not a Y. A Z.") → state Z.
- **Dramatic fragmentation** ("One model. One. And it won.") → complete sentences.
- **Rhetorical setups**: "What if we could…?", "Here's the key insight:". Make the point.
- **Vague declaratives**: "the implications are significant", "this has profound
  consequences". Name the specific implication.

## C. Rhythm — break the paper-by-paper cadence

The most recognizable survey-slop pattern is summary-by-summary prose: "Smith et al.
propose X. Jones et al. propose Y. Brown et al. propose Z." Even when the content is
thematic, the *sentence rhythm* can stay monotone and machine-like.

- Do not open three consecutive sentences with "Author et al." + verb. Group papers by
  what they share, then attribute: "Spectral methods (FNO, AFNO, FFNO) all replace the
  spatial kernel with an FFT; they differ in how they truncate modes."
- Vary sentence and paragraph length (2–8 sentences); mix short claims with longer
  compound ones.
- Do not end every paragraph on a punchy one-liner — that cadence reads as generated.
- Avoid stock transitions on autopilot: "Building on this…", "To address this
  limitation…", "Another line of work…". Use them sparingly and only when literally true.

## D. Survey-specific discipline

- **Attribute, don't abstract.** Every claim about "the field" traces to named papers
  (§B). This is both an anti-AI-tell rule and good scholarship.
- **Numbers, not adjectives**, for results. No "outperforms / improves / achieves SOTA"
  without the figure **and** seed/variance (or a note that variance was not reported —
  itself a finding, see §B vague gaps).
- **No "well-known that / it is clear that / obviously"** hand-waves — cite or drop.
- **Voice**: active for what the review does ("We organize methods by…", "This review
  covers…"); past tense and narrative attribution for prior work ("Li et al. showed…").
- Drop "to the best of our knowledge"; state the search end-date and scope instead.

## E. Academic exceptions (relax these stop-slop rules)

`stop-slop` is written for essays. Do **not** carry these rules into a survey:

- **Passive voice is allowed** where the actor is conventional or irrelevant: "FNO was
  evaluated on Burgers, Darcy, and Navier-Stokes." Prefer active + attribution for
  claims about who did what. Do not hunt down every passive.
- **Keep technical adverbs**: "asymptotically", "almost surely", "uniformly", "i.i.d.",
  "resolution-invariant". Cut only empty intensifiers (§A).
- **No second person.** Never "you" or "put the reader in the room" — survey register is
  first-person-plural / third-person. This stop-slop rule is inverted here.
- **Three-item lists are fine** (three method families, three benchmarks). Ignore
  stop-slop's "two beats three."
- **Em-dashes**: ≤ 2 per page, not a total ban.

## Per-paragraph checklist (fast pass)

1. Any phrase from §A (incl. puffery adjectives)? Cut or replace with the specific Δ.
2. Any "the literature reveals" / "research has shown" / "challenges remain"? Attribute
   to named papers or name the specific gap (§B).
3. Three sentences in a row = "Author et al. propose…"? Regroup thematically (§C).
4. Any result claim ("outperforms") without a number + variance? Add it or flag the gap.
5. Active voice + attribution for our claims; passive only where conventional (§D, §E).

## Precedence

Citation accuracy (Phase 7 verification) and the venue's citation style **override**
anything here — never trade correctness for fluency.
