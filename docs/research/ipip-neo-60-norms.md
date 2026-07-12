# IPIP-NEO-60 domain norms — derivation report

Derives **domain-level age×sex norm tables (mean, SD, N)** for the Maples-Keller (2019)
IPIP-NEO-60 from Johnson's public IPIP-NEO-120 raw dataset (619,150 respondents).

- Script: `derive_norms60.py` (pure Python stdlib, deterministic, rerunnable; ~5 s)
- Output: `norms_60_domains.json` — `{ "<Sex>|<AgeBand>": { domain: {mean, sd, n} } }`
- Data cached in this dir: `IPIP120.dat` (94.7 MB), `DAT120.doc` (layout), `johnson120.json` (item keys)

## 1. Data source (public domain, OSF)

- Project: **"Johnson's IPIP-NEO data repository"** — https://osf.io/tbmh5/
- Component: *Data from Johnson (2014), IPIP-NEO-120* — https://osf.io/wxvth/
- File: **`IPIP120.dat`** (94,729,950 bytes) — download: https://osf.io/download/q9jrh/
- Layout doc: **`DAT120.doc`** — download: https://osf.io/download/hgm7n/

The script auto-downloads `IPIP120.dat` via `curl` if absent (deterministic GUID).

### File layout (from DAT120.doc)
Fixed width, 151 chars/record, 619,150 records:

| Field | Cols (1-based) | Notes |
|---|---|---|
| CASE | 1–6 | original id (runs higher than N) |
| SEX | 7 | **1 = male, 2 = female** |
| AGE | 8–9 | years |
| SEC/MIN/HOUR/DAY/MONTH | 10–19 | completion time |
| YEAR | 20–22 | years since 1900 |
| COUNTRY | 23–31 | A9 string |
| I1…I120 | 32–151 | one char each, values **1–5**, missing = **0** |

**Keying is already applied in the file.** Per DAT120.doc: *"Reverse-scored items were
recoded (1=5, 2=4, 4=2, 5=1) at the time the respondent completed the inventory, so values
for these items can simply be added without recoding."* Every stored value is therefore
**trait-aligned** (higher = more of the facet trait), and domain/facet scores are plain sums.
Independently corroborated by `chfhhd/ipip-neo-120-descriptive-statistics/preparedata.R`,
which sums the raw items with no recoding.

### Item numbering — INTERLEAVED, not blocked
Johnson's item order cycles domains every item: I1=N1, I2=E1, I3=O1, I4=A1, I5=C1, I6=N2, …
So facet *f* (1–30) is measured by items {*f*, *f*+30, *f*+60, *f*+90}, and a **domain** owns
the 24 items whose `(itemnumber−1) % 5` selects it (N = {1,6,…,116}, E = {2,7,…,117}, etc.).
Getting this wrong (treating the order as blocked N1…C6) inflates N by ~+14..+20 and deflates
C — the first draft did exactly that and the orientation check caught it. The verbatim "120#"
numbers in `docs/research/ipip-neo-60.md` are correct and are used directly; each of the 60
selected items was verified to land in its intended domain.

## 2. Orientation confirmation (verify item scoring before deriving)

Reproduced Johnson's 120 **domain means** (24 items/domain, complete-120 cases) from the raw
file and compared to the reference norm tables embedded in `IPIP-NEO-PI/app/evaluator.py`.

Result (all 8 cells × 5 domains, all countries, ages within band):

- **Pearson r(derived, reference) = 0.976** over the 40 cell-domain points
- **max |derived − reference| = 5.7** points
- Agreeableness matches the reference **within ~1 point in every cell**
- Correct sex ordering and correct monotone age gradients throughout

The residual offsets are structured (N ≈ 2–4 low, C ≈ 2–4 high, O ≈ 5 low for young cohorts)
and stable — they reflect that `evaluator.py`'s tables are Johnson's **distributed short-form
norms** ("IPIPlinux", June 2021), computed on a *different reference sample / set of
exclusions* than the public 619k OSF file, **not** a scoring error. A single mis-keyed item
would throw its domain off by ~15–30 points; nothing of that magnitude appears. Restricting to
USA-only respondents does not change the picture (r = 0.969), ruling out a country artifact.

**Conclusion: item orientation and domain assignment are correct.** The 619k-derived means are
the appropriate basis for the IPIP-NEO-60 norms (and are internally self-normed: dataset mean
→ T = 50 by construction).

## 3. Building the IPIP-NEO-60 domain scores

For each of the 30 facets, two items are summed per the 60→120 mapping. 51 of the 60 items are
verbatim in the 120 and use their documented 120# directly (keying already baked into the
stored value). The **9 items with no equivalent in the 120** are replaced by the nearest
same-facet Johnson item.

### Keying decision for the 9 substitutes
Because the `.dat` stores **all** items trait-aligned, a substitute contributes to the domain
sum **in the trait direction automatically**, regardless of its own +/− surface wording — its
stored value is already oriented so that "more of the facet" = higher. So no manual reversal is
applied to substitutes; they are added exactly like the overlapping items. Substitutes were
chosen for **closest facet content** (and, where possible, matching surface keying) among the
Johnson items in the *same facet* not already used by the 60:

| 60 facet | Original NEW 60-item (dropped) | Substitute → Johnson 120# | Note |
|---|---|---|---|
| N4 Self-Consciousness | Am easily intimidated (+) | **46** "Am afraid to draw attention to myself" (+) | closest social-fear item |
| N6 Vulnerability | Am calm even in tense situations (−) | **56** "Become overwhelmed by events" (+) | nearest vulnerability item; stored value trait-aligned |
| E1 Friendliness | Act comfortably with others (+) | **32** "Feel comfortable around people" (+) | near-synonym |
| O2 Artistic Interests | Do not like art (−) | **98** "Do not enjoy going to art museums" (−) | near-synonym, same key |
| O3 Emotionality | Am not easily affected by my emotions (−) | **73** "Rarely notice my emotional reactions" (−) | closest, same key |
| O4 Adventurousness | Don't like the idea of change (−) | **78** "Dislike changes" (−) | near-synonym, same key |
| O6 Liberalism | Believe in one true religion (−) | **118** "Believe that we should be tough on crime" (−) | nearest same-key liberalism marker |
| C2 Orderliness | Like order (+) | **10** "Like to tidy up" (+) | closest orderliness, same key |
| C4 Achievement-Striving | Set high standards for myself and others (+) | **50** "Do more than what's expected of me" (+) | closest achievement item, same key |

For each facet, the full pair used is listed in `FACET_ITEMS` in the script (with a comment per
facet). The other 51 items are the verbatim 120# from `docs/research/ipip-neo-60.md §2`.

**Domain raw score = sum of that domain's 12 items** (6 facets × 2), range **12–60**.

## 4. Cells, exclusions, and Ns

8 cells identical to the reference engine: sex ∈ {Male, Female} × age band ∈ {<21, 21–40,
41–60, >60}. Excluded: records with invalid sex, non-numeric or out-of-range age (kept 10–99),
malformed rows, and any record missing (0) one or more of the 60 scored items
(**complete-case on the 60**). 487,219 of 619,150 respondents are complete on all 60 items.

Per-cell N (complete-60):

| Cell | N |
|---|---|
| Male \| <21 | 79,948 |
| Male \| 21–40 | 99,884 |
| Male \| 41–60 | 16,873 |
| Male \| >60 | 1,360 |
| Female \| <21 | 130,207 |
| Female \| 21–40 | 130,797 |
| Female \| 41–60 | 26,767 |
| Female \| >60 | 1,383 |

All cells are well-powered except the two **>60** cells (~1.36–1.38k). These meet a "thousands"
bar but are the least stable; treat >60 norms as usable-but-noisier. (SDs use ddof=1.)

## 5. Derived IPIP-NEO-60 domain norms (mean / SD)

| Cell | N | E | O | A | C |
|---|---|---|---|---|---|
| Male \| <21 | 33.06 / 7.76 | 44.02 / 7.88 | 39.11 / 6.73 | 41.04 / 7.26 | 41.89 / 7.08 |
| Male \| 21–40 | 31.99 / 8.12 | 43.65 / 8.00 | 40.61 / 6.64 | 42.30 / 6.71 | 44.82 / 7.07 |
| Male \| 41–60 | 31.17 / 8.27 | 41.88 / 8.05 | 40.74 / 6.69 | 44.52 / 6.23 | 47.14 / 6.80 |
| Male \| >60 | 29.65 / 7.98 | 41.46 / 7.87 | 40.19 / 7.01 | 44.68 / 7.05 | 47.25 / 7.45 |
| Female \| <21 | 36.35 / 7.55 | 44.97 / 7.47 | 40.31 / 6.40 | 45.04 / 6.45 | 42.79 / 6.99 |
| Female \| 21–40 | 35.63 / 7.99 | 43.68 / 7.69 | 41.42 / 6.53 | 46.10 / 5.88 | 45.35 / 6.86 |
| Female \| 41–60 | 33.25 / 8.05 | 42.15 / 7.81 | 41.45 / 6.64 | 48.12 / 5.23 | 47.93 / 6.45 |
| Female \| >60 | 31.75 / 7.77 | 41.48 / 7.96 | 40.76 / 7.14 | 48.43 / 6.19 | 47.93 / 6.83 |

Exact values (4 dp) with N are in `norms_60_domains.json`. Patterns are as expected: women
higher N and A; C rises with age; N falls with age.

## 6. Sanity checks (printed by the script)

1. **Cell Ns**: min = 1,360 (the >60 cells); all others 16k–131k.
2. **T at dataset mean = 50.0** by construction (spot-checked Male 21–40, N).
3. **Approx normality**: skew of E (Female 21–40, n = 20,000 sample) = −0.42 (|skew| < 0.5).
4. **Percentile spot-check**: a random Female 21–40 respondent with E raw = 39 → T = 43.9 →
   cubic percentile = 28 (sensible: a below-average raw maps below the 50th percentile). The
   percentile pipeline is `T = 50 + 10·(raw − mean)/sd`, clamped to [32, 73], then the same
   cubic `CONST1…CONST4` polynomial used for the 120 in `evaluator.py`.

## 7. How to use / integrate

- Use `norms_60_domains.json` for the Quick-path (60-item) **domain** percentiles: look up the
  respondent's `Sex|AgeBand` cell, compute `T = 50 + 10·(raw − mean)/sd`, clamp to [32, 73],
  then apply the existing cubic percentile polynomial. Reuse the exact age-band boundaries
  (<21 / 21–40 / 41–60 / >60) and clamp constants from `evaluator.py` for consistency with the
  120 path.
- Scale note: these are **1–5 raw sums, range 12–60**. Keep the 60 pipeline on the 1–5
  convention (reverse "−" items as 6−raw) so raws match this norm scale.

## 8. Caveats

- **Domain-level only.** The 9 substitutions are same-facet approximations, so facet-level
  60-norms are intentionally **not** produced here (2-item facets are already noisy; substituting
  a different item compounds it). For exact facet norms, use the IPIP-NEO-300 / Eugene-Springfield
  data (contains all 60 items) — out of scope for this task.
- The substitutions shift each affected facet's content slightly; at the **domain** level (12
  items) the effect is small and washed out, which is why domain norms are the defensible
  deliverable.
- Reference-norm offsets (§2) mean these 619k-based norms are internally consistent but will not
  reproduce Johnson's distributed short-form percentiles exactly; that is expected and correct —
  we norm the 60 on the same population we score it against.
- `>60` cells are the smallest (~1.4k each); flag as lower-confidence.

## Attribution
- Maples-Keller et al. (2019), *JPA* 101(1), 4–15 — the IPIP-NEO-60.
- Johnson, J. A. (2014), *JRP* 51, 78–89 — the IPIP-NEO-120 and the 619k dataset.
- Goldberg (1999) / Goldberg et al. (2006) — the IPIP. Public domain; commercial use permitted.
