# IPIP-NEO-60 Short Form — Research Report

Research for the "Quick (~10 min)" test path of the Big Five app. Companion to the existing
IPIP-NEO-120 (Johnson, 2014) implementation.

**Bottom line:** A validated, public-domain, facet-representative 60-item IPIP-NEO short form
exists — the **Maples-Keller et al. (2019) IPIP-NEO-60** — and its exact item list, facets, and
keying are freely published on ipip.ori.org. It is **not** a strict subset of Johnson's 120
(51 of 60 items overlap), and **no age/sex norm tables were published** for it. Recommendation:
adopt the Maples-Keller 60 as its own instrument with its own scoring, and derive percentile
norms ourselves from Johnson's public OSF dataset by re-scoring the 60-item subscales in that
data. See [Recommendation](#7-recommendation-quick-path).

---

## 1. Which validated 60-item IPIP-NEO short forms exist?

### The one to use: Maples-Keller et al. (2019) IPIP-NEO-60

- **Full citation:** Maples-Keller, J. L., Williamson, R. L., Sleep, C. E., Carter, N. T.,
  Campbell, W. K., & Miller, J. D. (2019). *Using item response theory to develop a 60-item
  representation of the NEO PI–R using the International Personality Item Pool: Development of
  the IPIP–NEO–60.* Journal of Personality Assessment, 101(1), 4–15.
  DOI: [10.1080/00223891.2017.1381968](https://doi.org/10.1080/00223891.2017.1381968)
- **Derivation:** Item Response Theory (IRT) selection of **2 items per facet** from the broader
  IPIP item pool, giving **equal representation** of all 30 NEO PI–R facets
  (5 domains × 6 facets × 2 items = 60). Validated against the NEO-FFI, NEO PI–R, and
  IPIP-NEO-300 in an undergraduate sample (n = 359) and the Eugene-Springfield community sample
  (n = 757).
- **Psychometrics (Eugene-Springfield community sample, N = 757):** domain coefficient alphas
  N = .95, E = .92, O = .92, A = .90, C = .92 (per the ipip.ori.org scoring-key page).
- **Authoritative item list & keys (public, free):**
  - Scoring keys (all 60 items, facet + keying, verbatim):
    <https://ipip.ori.org/IPIP-NEO-60ScoringKeys.htm>
  - Comparison table (reliability/validity stats only, no item numbers):
    <https://ipip.ori.org/IPIP-NEO-60ComparisonTable.htm>
  - Index page listing it among multi-construct IPIP inventories:
    <https://ipip.ori.org/newMultipleconstructs.htm>

This is the instrument to implement. Its full item text is reproduced in
[Section 2](#2-the-exact-60-items).

### Distinguishing it from other 60-item Big Five instruments

- **NEO-FFI-60 (Costa & McCrae) — DO NOT USE.** The NEO-FFI is a 60-item proprietary,
  **copyrighted** instrument published by PAR. Its items are not public domain. Maples-Keller's
  whole point was to build a public-domain IPIP replacement that behaves like the NEO-FFI —
  so we get NEO-FFI-like coverage without touching copyrighted items.
  (Ref: [Revised NEO Personality Inventory — Wikipedia](https://en.wikipedia.org/wiki/Revised_NEO_Personality_Inventory).)
- **Other public Big Five short forms** (BFI-2, Mini-IPIP 20-item, IPIP-BFM, etc.) exist but are
  **not** NEO-facet instruments and don't align with our 30-facet 120-item architecture. The
  Maples-Keller 60 is the only widely-cited, validated, **facet-level** 60-item IPIP-NEO.

---

## 2. The exact 60 items

Reproduced verbatim from <https://ipip.ori.org/IPIP-NEO-60ScoringKeys.htm>. Grouped
domain → facet; each facet has exactly 2 items. "+/−" = keying. The "120#" column shows the
matching item number in Johnson's IPIP-NEO-120 where the text is identical (see
[Section 3](#3-is-it-a-subset-of-the-ipip-neo-120)); **NEW** = item does not appear in the 120.

### Neuroticism (α = .95)

| Facet | Key | Item text | 120# |
|---|---|---|---|
| N1 Anxiety | + | Worry about things. | 1 |
| N1 Anxiety | + | Get stressed out easily. | 91 |
| N2 Anger | + | Get angry easily. | 6 |
| N2 Anger | + | Lose my temper. | 66 |
| N3 Depression | + | Often feel blue. | 11 |
| N3 Depression | + | Dislike myself. | 41 |
| N4 Self-Consciousness | + | Find it difficult to approach others. | 16 |
| N4 Self-Consciousness | + | Am easily intimidated. | **NEW** |
| N5 Immoderation | − | Rarely overindulge. | 51 |
| N5 Immoderation | − | Am able to control my cravings. | 111 |
| N6 Vulnerability | − | Remain calm under pressure. | 116 |
| N6 Vulnerability | − | Am calm even in tense situations. | **NEW** |

### Extraversion (α = .92)

| Facet | Key | Item text | 120# |
|---|---|---|---|
| E1 Friendliness | + | Make friends easily. | 2 |
| E1 Friendliness | + | Act comfortably with others. | **NEW** |
| E2 Gregariousness | + | Love large parties. | 7 |
| E2 Gregariousness | − | Avoid crowds. | 97 |
| E3 Assertiveness | + | Take charge. | 12 |
| E3 Assertiveness | + | Try to lead others. | 42 |
| E4 Activity Level | + | Am always busy. | 17 |
| E4 Activity Level | + | Am always on the go. | 47 |
| E5 Excitement-Seeking | + | Love excitement. | 22 |
| E5 Excitement-Seeking | + | Seek adventure. | 52 |
| E6 Cheerfulness | + | Have a lot of fun. | 57 |
| E6 Cheerfulness | + | Love life. | 87 |

### Openness to Experience (α = .92)

| Facet | Key | Item text | 120# |
|---|---|---|---|
| O1 Imagination | + | Have a vivid imagination. | 3 |
| O1 Imagination | + | Love to daydream. | 63 |
| O2 Artistic Interests | + | Believe in the importance of art. | 8 |
| O2 Artistic Interests | − | Do not like art. | **NEW** |
| O3 Emotionality | + | Experience my emotions intensely. | 13 |
| O3 Emotionality | − | Am not easily affected by my emotions. | **NEW** |
| O4 Adventurousness | − | Prefer to stick with things that I know. | 48 |
| O4 Adventurousness | − | Don't like the idea of change. | **NEW** |
| O5 Intellect | − | Avoid philosophical discussions. | 53 |
| O5 Intellect | − | Am not interested in theoretical discussions. | 113 |
| O6 Liberalism | + | Tend to vote for liberal political candidates. | 28 |
| O6 Liberalism | − | Believe in one true religion. | **NEW** |

### Agreeableness (α = .90)

| Facet | Key | Item text | 120# |
|---|---|---|---|
| A1 Trust | + | Trust others. | 4 |
| A1 Trust | + | Believe that others have good intentions. | 34 |
| A2 Morality | − | Cheat to get ahead. | 39 |
| A2 Morality | − | Take advantage of others. | 69 |
| A3 Altruism | + | Love to help others. | 14 |
| A3 Altruism | + | Am concerned about others. | 44 |
| A4 Cooperation | − | Insult people. | 79 |
| A4 Cooperation | − | Get back at others. | 109 |
| A5 Modesty | − | Believe that I am better than others. | 24 |
| A5 Modesty | − | Think highly of myself. | 54 |
| A6 Sympathy | + | Sympathize with the homeless. | 29 |
| A6 Sympathy | + | Feel sympathy for those who are worse off than myself. | 59 |

### Conscientiousness (α = .92)

| Facet | Key | Item text | 120# |
|---|---|---|---|
| C1 Self-Efficacy | + | Handle tasks smoothly. | 65 |
| C1 Self-Efficacy | + | Know how to get things done. | 95 |
| C2 Orderliness | + | Like order. | **NEW** |
| C2 Orderliness | − | Leave a mess in my room. | 70 |
| C3 Dutifulness | + | Tell the truth. | 45 |
| C3 Dutifulness | − | Break my promises. | 105 |
| C4 Achievement-Striving | + | Work hard. | 20 |
| C4 Achievement-Striving | + | Set high standards for myself and others. | **NEW** |
| C5 Self-Discipline | + | Carry out my plans. | 55 |
| C5 Self-Discipline | − | Have difficulty starting tasks. | 115 |
| C6 Cautiousness | − | Make rash decisions. | 60 |
| C6 Cautiousness | − | Act without thinking. | 120 |

**Reverse-keyed count:** 24 of 60 items are negatively keyed (marked "−" above).

---

## 3. Is it a subset of the IPIP-NEO-120?

**No — it is a partial overlap, not a strict subset.** 51 of the 60 items appear verbatim (same
text, same keying, same facet) in Johnson's IPIP-NEO-120; **9 items are new**, drawn from the
wider IPIP / IPIP-NEO-PI-R pool rather than Johnson's specific 120-item selection.

- **51/60 match**, with **zero keying conflicts** — every overlapping item keeps the same +/−
  direction in both instruments.
- Johnson's convention: facet *f* (1..30, ordered N1..C6) is measured by items {*f*, *f*+30,
  *f*+60, *f*+90}. Every matched 60-item lands in the expected facet, using 2 of the 4 items
  that Johnson assigns to that facet. So the 60 is *mostly* "pick 2 of Johnson's 4 per facet,
  plus 9 substitutions."
- **The 9 items with no equivalent in the 120** (verified absent — none of the 4 Johnson items
  in the facet matches the text):
  - N4 "Am easily intimidated"
  - N6 "Am calm even in tense situations"
  - E1 "Act comfortably with others"
  - O2 "Do not like art"
  - O3 "Am not easily affected by my emotions"
  - O4 "Don't like the idea of change"
  - O6 "Believe in one true religion"
  - C2 "Like order"
  - C4 "Set high standards for myself and others"

**Sources used for the 120-item numbering** (two independent machine-readable lists,
cross-agreeing on 119/120 items — the one difference is a cosmetic wording variant on item #58
that affects none of the 60):

- `zrrrzzt/b5-johnson-120-ipip-neo-pi-r` → `examples/items-en.json`
  (<https://github.com/zrrrzzt/b5-johnson-120-ipip-neo-pi-r>)
- `NeuroQuestAi/five-factor-e` → `data/IPIP-NEO/120/questions.json`
  (<https://github.com/NeuroQuestAi/five-factor-e>)

**Implication:** We cannot implement the Quick path as "serve items {a, b} of each 120 facet and
reuse the 120 norms." 9 items would be missing, and — more fundamentally — the scoring scale
differs (see next section).

---

## 4. Scoring specification

The Maples-Keller 60 is scored at **both facet and domain level**, exactly parallel to the 120
but on a 2-item facet scale instead of 4:

- **Response scale:** 5-point Likert, "Very Inaccurate" → "Very Accurate", scored 1–5 (or 0–4;
  be internally consistent — the 120 pipeline's choice should be mirrored).
- **Reverse scoring:** for each "−" keyed item, reverse before summing (on a 1–5 scale,
  reversed = 6 − raw).
- **Facet score:** sum of the 2 items in that facet. Range 2–10 (1–5 scale) — max 8 points
  above floor. (Some third-party sites use 0–4 scoring, giving a facet range 0–8.)
- **Domain score:** sum of that domain's 12 items (6 facets × 2). Range 12–60 (1–5 scale).
- **Percentile / T-score presentation:** the raw domain/facet sum is converted to a
  norm-referenced percentile. Maples-Keller do not prescribe a percentile pipeline; the app
  supplies that (see [Section 5](#5-norms-availability)).

**Caveat on facet reliability:** 2-item facet scores are inherently noisy (facet reliabilities
are low by construction). The paper validates the instrument primarily at the **domain** level.
Present domain scores as the headline result; treat facet scores as indicative only, and
consider hiding or caveating facet-level percentiles on the Quick path.

---

## 5. Norms availability

**Verdict: No published age/sex norm tables exist for the Maples-Keller IPIP-NEO-60. We must
generate our own — which is legitimate and straightforward given the public data.**

- **IPIP publishes no norms at all**, by policy: *"No norms are available on the IPIP website…"*
  and it recommends local norms.
  (<https://ipip.ori.org/newNorms.htm>)
- **Maples-Keller (2019)** report reliability/validity and correlations, and use the community
  sample (N = 757) and undergraduate sample (N = 359), but **do not publish normative
  means/SDs by age and sex** suitable for a percentile engine. (Abstract confirmed via
  [ResearchGate](https://www.researchgate.net/publication/320745867) and
  [Semantic Scholar](https://www.semanticscholar.org/paper/c6d097fbcb6c58a539b42b29c3d7287ae2894977);
  full text paywalled at [T&F](https://doi.org/10.1080/00223891.2017.1381968).)
- **Johnson's 120 norms** (already in our plan) are **not directly reusable** for the 60: even
  for the 51 overlapping items, each facet in the 60 has 2 items vs 4 in the 120, so raw
  facet/domain sums are on a different scale — Johnson's facet/domain norm tables would be off
  by construction, and 9 items aren't in his data at all at the item level.

**The clean path: derive our own 60-item norms from Johnson's public raw dataset.**

- Johnson released the item-level responses behind the 120 on the **Open Science Framework**
  (the same ~300k–600k respondent dataset our 120 percentiles come from). See the data links
  from <https://ipip.ori.org/newNorms.htm> and Johnson's OSF project.
- **But**: that dataset contains responses to the **120** items. It covers the **51 overlapping**
  60-items directly. It does **not** contain the **9 new** items — so we cannot fully reconstruct
  all 30 two-item facet scores from Johnson's 120 data alone.
- Two workable options:
  1. **Domain-level norms from Johnson's 120 data, restricted to overlapping items.** For the 9
     new items' facets, substitute the nearest Johnson item in the same facet (documented
     approximation) so all 12 items per domain are populated, then compute domain
     means/SDs by age×sex and build the same T-score → percentile mapping used for the 120.
     Domains are the headline metric, so this yields defensible domain percentiles.
  2. **The larger IPIP-NEO-300 / Eugene-Springfield data** (Harvard Dataverse, linked from the
     IPIP norms page) contains the full IPIP-NEO-PI-R item pool and therefore **all 60 items**
     including the 9 new ones — enabling exact 60-item facet and domain norms. This is the more
     rigorous route if facet-level percentiles are wanted.
- Whichever dataset, **build norms by re-scoring the actual 60 subscale items in the raw data**
  (per age × sex cells, mirroring the 8 cells the 120 uses), then reuse the existing
  T-score → percentile (cubic) machinery. Document the derivation.

---

## 6. Licensing

**Clean — public domain, commercial use allowed, no permission required.**

Official IPIP statement (<https://ipip.ori.org/newPermission.htm>):

> "Because the IPIP has been placed in the public domain, permission has already been
> automatically granted for any person to use IPIP items, scales, and inventories for any
> purpose, commercial or non-commercial." … "It is not necessary to contact the IPIP site author
> (Lew Goldberg) or the IPIP Consultant (John A. Johnson) for permission to use IPIP materials."

- **No copyrighted NEO items are involved.** The Maples-Keller 60 is 100% IPIP items. We must
  keep it that way — do **not** import any NEO-FFI / NEO PI-R item text.
- **Attribution:** not legally required, but best practice and good for credibility. Cite:
  - Maples-Keller et al. (2019), JPA 101(1), 4–15, DOI 10.1080/00223891.2017.1381968 (the 60).
  - Goldberg, L. R. (1999) / Goldberg et al. (2006) for the IPIP itself.
  - Johnson, J. A. (2014), JRP 51, 78–89 (the 120, if we reuse its data/norms).

---

## 7. Recommendation (Quick path)

**Implement the Maples-Keller (2019) IPIP-NEO-60 as a first-class second instrument, with its own
item set and its own norms — not as a subset view of the 120.**

Concretely:

1. **Items.** Ship all 60 items exactly as in [Section 2](#2-the-exact-60-items) (verbatim from
   the ipip.ori.org scoring key). Store facet + keying per item. 24 are reverse-keyed. Do not try
   to reuse the 120's item file — 9 items aren't in it.
2. **Scoring.** Domain = sum of 12 items; facet = sum of 2 items; reverse "−" items first
   (6 − raw on a 1–5 scale). Mirror the 120 pipeline's raw-scale convention for consistency.
   Lead with **domain** scores; caveat or de-emphasize 2-item facet percentiles.
3. **Norms.** Generate our own from Johnson's public OSF 120-item dataset (Option 1: domain-level
   norms, using the 51 overlapping items + documented same-facet substitutes for the 9 new ones),
   reusing the existing age×sex cells and the T-score → cubic-percentile conversion. If
   facet-level percentiles on the Quick path are a hard requirement, upgrade to the IPIP-NEO-300 /
   Eugene-Springfield raw data (Harvard Dataverse), which contains all 60 items. Document the
   choice and its limits in-app.
4. **Licensing / attribution.** No blockers. Add a credits line citing Maples-Keller (2019),
   Goldberg (IPIP), and Johnson (2014, for the norm data).
5. **UX framing.** Market it honestly as a validated ~10-minute short form of the same Big Five /
   NEO facet model, with the caveat that facet-level detail is coarser than the full 120.

**Fallback if we want zero norm-derivation work now:** serve the 60 items, compute and display
**raw domain scores + our own sample-based percentiles later**, or run the full 120 with a
"quick" progress UX. But deriving domain norms from Johnson's existing dataset is low-effort given
we're already ingesting it for the 120, so the first-class 60 is the recommended path.

### Open items to close during implementation
- Decide 0–4 vs 1–5 raw scoring and keep it identical to the 120 pipeline.
- Pick the norm dataset (Johnson 120 OSF vs Eugene-Springfield 300) per whether facet percentiles
  are required on the Quick path.
- Pull the exact OSF / Harvard Dataverse dataset URLs from <https://ipip.ori.org/newNorms.htm>
  when wiring up norm generation.

---

## Sources

- IPIP-NEO-60 scoring keys (authoritative item list): <https://ipip.ori.org/IPIP-NEO-60ScoringKeys.htm>
- IPIP-NEO-60 comparison table: <https://ipip.ori.org/IPIP-NEO-60ComparisonTable.htm>
- IPIP multi-construct inventories index: <https://ipip.ori.org/newMultipleconstructs.htm>
- IPIP permission / public-domain statement: <https://ipip.ori.org/newPermission.htm>
- IPIP norms policy: <https://ipip.ori.org/newNorms.htm>
- Maples-Keller et al. (2019), DOI: <https://doi.org/10.1080/00223891.2017.1381968>
- Paper abstract (ResearchGate): <https://www.researchgate.net/publication/320745867>
- Paper (Semantic Scholar): <https://www.semanticscholar.org/paper/c6d097fbcb6c58a539b42b29c3d7287ae2894977>
- Johnson 120 item list (cross-check): <https://github.com/zrrrzzt/b5-johnson-120-ipip-neo-pi-r>
- Johnson 120 item list (cross-check): <https://github.com/NeuroQuestAi/five-factor-e>
- NEO-FFI copyright context: <https://en.wikipedia.org/wiki/Revised_NEO_Personality_Inventory>
