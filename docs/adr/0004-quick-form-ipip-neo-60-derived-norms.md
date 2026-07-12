# Quick form: IPIP-NEO-60 (Maples-Keller 2019) with derived domain norms

The Quick (~10 min) path uses the **Maples-Keller et al. (2019) IPIP-NEO-60**, a validated,
public-domain 60-item short form (2 items per facet, equal representation of all 30 NEO facets).
Its exact item list and keying are freely published on ipip.ori.org.
Citation: Maples-Keller, J. L., Williamson, R. L., Sleep, C. E., Carter, N. T., Campbell, W. K.,
& Miller, J. D. (2019), *Journal of Personality Assessment*, 101(1), 4–15,
DOI [10.1080/00223891.2017.1381968](https://doi.org/10.1080/00223891.2017.1381968).
Full sourcing and item text: `docs/research/ipip-neo-60.md`.

## Decisions

- **Own instrument, not a subset of the 120.** Only 51 of the 60 items overlap Johnson's
  IPIP-NEO-120, and the two forms were IRT-selected independently. Quick is scored as its own
  instrument with its own item bank and keying — we do **not** try to reuse 120 scoring for it.
- **Raw scale 1–5, matching Full.** The slider and per-item keying work exactly as on the Full
  form; only the item set and length differ.
- **Derived norms, because none are published.** Maples-Keller published no age/sex norm tables.
  We derive **domain-level** age×sex norms ourselves by re-scoring the 60-item subscales in
  Johnson's public OSF IPIP-NEO-120 dataset (N ≈ 619k), giving means/SDs per (sex, age band) that
  plug into the same `T = 50 + 10·(raw−mean)/sd` → cubic-percentile pipeline. Method detailed in
  `docs/research/ipip-neo-60.md`.
- **Quick report is domain-only.** With 2 items per facet, facet scores are too unreliable to
  report. The Quick report ships **five domain percentiles only** — 2-item facet percentiles are
  never computed or shown. (The Full form remains domain + 30 facets.)

## Consequences

- The scoring engine gains a Quick path (`app/scoring/engine_quick.py`) that shares the
  keying/T-score/percentile machinery but loads a separate 60-item bank
  (`app/scoring/data/ipip_neo_60.json`) and a separate domain-only norm set
  (`app/scoring/data/norms_60_domains.json`, derived by `backend/scripts/derive_norms60.py`;
  method in `docs/research/ipip-neo-60-norms.md`).
- Landed in PR6: `GET /forms/quick/items` serves the 60 items (keying stripped) and
  `POST /test-runs` accepts `form="quick"`; completion scores domain-only. The start-screen Quick
  card is selectable.
- **Keying count.** The source's prose summary says "24 of 60 items are negatively keyed," but the
  authoritative per-item scoring key (ipip.ori.org) and the research doc's own item table both
  enumerate exactly **23** reverse-keyed items. The bank uses the verified per-item keying (23); we
  did not invent a 24th reverse item.
- No copyrighted items are used: the NEO-FFI-60 is explicitly rejected in favour of the
  public-domain IPIP replacement.
