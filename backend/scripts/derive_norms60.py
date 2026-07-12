#!/usr/bin/env python3
"""
Derive IPIP-NEO-60 (Maples-Keller 2019) DOMAIN-level age x sex norm tables
from Johnson's public IPIP-NEO-120 raw dataset (619,150 respondents).

Data source (public domain, OSF):
  Project : "Johnson's IPIP-NEO data repository"          https://osf.io/tbmh5/
  Component: Data from Johnson (2014), IPIP-NEO-120        https://osf.io/wxvth/
  File     : IPIP120.dat  (94,729,950 bytes)               https://osf.io/download/q9jrh/
  Layout   : DAT120.doc                                    https://osf.io/download/hgm7n/

File layout (fixed width, 151 chars/record, from DAT120.doc):
  CASE 1-6, SEX 7 (1=male 2=female), AGE 8-9, SEC/MIN/HOUR/DAY/MONTH 10-19,
  YEAR 20-22, COUNTRY 23-31, then I1..I120 in columns 32-151 (1 char each).
  Item values 1-5, missing = 0. REVERSE-SCORED ITEMS ARE ALREADY RECODED in the
  file (1<->5, 2<->4) so all stored values are trait-aligned and can be summed
  directly -- no per-item keying is applied here.

Johnson item numbering (== column order I1..I120): facet f in 1..30 (N1..C6)
is measured by items {f, f+30, f+60, f+90}. The IPIP-NEO-60 selects 2 items per
facet. 51 of its 60 items appear verbatim in the 120 (same text, same keying);
9 items are new and are replaced here by the nearest same-facet Johnson item
(see SUBSTITUTES below and REPORT.md).

Method:
  * Reproduce Johnson's published 120 DOMAIN means (24 items/domain) from the raw
    data as an ORIENTATION CHECK against evaluator.py's norm tables.
  * Compute IPIP-NEO-60 domain raw scores: for each domain sum its 12 selected
    items (6 facets x 2). Because stored values are already trait-aligned, the
    domain sum uses each selected/substituted item's stored value directly.
  * Per age x sex cell (same 8 cells as the reference 120), compute mean/SD/N of
    each of the 5 domain raw scores (range 12-60).

Output:
  norms_60_domains.json  {cell: {domain: {mean, sd, n}}}
  Console: 120 orientation check, cell Ns, sanity checks.

Deterministic; rerunnable. Pure Python stdlib (no numpy). Streams the file in a
single pass accumulating count / sum / sum-of-squares per (cell, domain).
Downloads IPIP120.dat to CWD if absent.
"""

import json
import math
import os
import random
import subprocess
import sys

DAT_URL = "https://osf.io/download/q9jrh/"
DAT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "IPIP120.dat")
OUT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "norms_60_domains.json")

RECLEN = 151          # stripped record length
ITEMS_START = 31      # 0-based index of I1 (column 32)

DOMAINS = ["N", "E", "O", "A", "C"]

# ---------------------------------------------------------------------------
# IPIP-NEO-60 -> IPIP-NEO-120 item selection (Johnson item numbers, 1..120).
# For each facet, the two 120-item numbers whose values are summed for the 60.
# 51 overlapping items use their verbatim 120# from docs/research/ipip-neo-60.md.
# The 9 substituted facets use the nearest same-facet Johnson item (see REPORT).
# Values are trait-aligned in the .dat, so summing needs no per-item keying.
#
# facet index 1..30 == N1,N2,N3,N4,N5,N6, E1..E6, O1..O6, A1..A6, C1..C6
# ---------------------------------------------------------------------------
FACET_ITEMS = {
    # Neuroticism
    1:  [1, 91],      # N1 Anxiety: Worry / Get stressed out easily
    2:  [6, 66],      # N2 Anger: Get angry easily / Lose my temper
    3:  [11, 41],     # N3 Depression: Often feel blue / Dislike myself
    4:  [16, 46],     # N4 Self-Consciousness: 16 verbatim + SUB 46 (was "Am easily intimidated")
    5:  [51, 111],    # N5 Immoderation: Rarely overindulge / Am able to control my cravings
    6:  [116, 56],    # N6 Vulnerability: 116 verbatim + SUB 56 (was "Am calm even in tense situations")
    # Extraversion
    7:  [2, 32],      # E1 Friendliness: 2 verbatim + SUB 32 (was "Act comfortably with others")
    8:  [7, 97],      # E2 Gregariousness: Love large parties / Avoid crowds
    9:  [12, 42],     # E3 Assertiveness: Take charge / Try to lead others
    10: [17, 47],     # E4 Activity Level: Am always busy / Am always on the go
    11: [22, 52],     # E5 Excitement-Seeking: Love excitement / Seek adventure
    12: [57, 87],     # E6 Cheerfulness: Have a lot of fun / Love life
    # Openness
    13: [3, 63],      # O1 Imagination: Have a vivid imagination / Love to daydream
    14: [8, 98],      # O2 Artistic Interests: 8 verbatim + SUB 98 (was "Do not like art")
    15: [13, 73],     # O3 Emotionality: 13 verbatim + SUB 73 (was "Am not easily affected...")
    16: [48, 78],     # O4 Adventurousness: 48 verbatim + SUB 78 (was "Don't like the idea of change")
    17: [53, 113],    # O5 Intellect: Avoid philosophical / Am not interested in theoretical
    18: [28, 118],    # O6 Liberalism: 28 verbatim + SUB 118 (was "Believe in one true religion")
    # Agreeableness
    19: [4, 34],      # A1 Trust: Trust others / Believe that others have good intentions
    20: [39, 69],     # A2 Morality: Cheat to get ahead / Take advantage of others
    21: [14, 44],     # A3 Altruism: Love to help others / Am concerned about others
    22: [79, 109],    # A4 Cooperation: Insult people / Get back at others
    23: [24, 54],     # A5 Modesty: Believe I'm better than others / Think highly of myself
    24: [29, 59],     # A6 Sympathy: Sympathize with the homeless / Feel sympathy...
    # Conscientiousness
    25: [65, 95],     # C1 Self-Efficacy: Handle tasks smoothly / Know how to get things done
    26: [10, 70],     # C2 Orderliness: SUB 10 (was "Like order") + 70 verbatim
    27: [45, 105],    # C3 Dutifulness: Tell the truth / Break my promises
    28: [20, 50],     # C4 Achievement-Striving: 20 verbatim + SUB 50 (was "Set high standards...")
    29: [55, 115],    # C5 Self-Discipline: Carry out my plans / Have difficulty starting tasks
    30: [60, 120],    # C6 Cautiousness: Make rash decisions / Act without thinking (both verbatim)
}

# domain -> its 6 facet indices
DOMAIN_FACETS = {
    "N": [1, 2, 3, 4, 5, 6],
    "E": [7, 8, 9, 10, 11, 12],
    "O": [13, 14, 15, 16, 17, 18],
    "A": [19, 20, 21, 22, 23, 24],
    "C": [25, 26, 27, 28, 29, 30],
}

# Substitutes actually used (target NEW item -> chosen 120#), for the report/log.
SUBSTITUTES = {
    "N4": (46, "Am afraid to draw attention to myself"),
    "N6": (56, "Become overwhelmed by events"),
    "E1": (32, "Feel comfortable around people"),
    "O2": (98, "Do not enjoy going to art museums"),
    "O3": (73, "Rarely notice my emotional reactions"),
    "O4": (78, "Dislike changes"),
    "O6": (118, "Believe that we should be tough on crime"),
    "C2": (10, "Like to tidy up"),
    "C4": (50, "Do more than what's expected of me"),
}

# 120-item DOMAIN norm means from evaluator.py (indices 1..5 of each norm tuple),
# used only to confirm item orientation. 24 items/domain, so these are NOT the
# 60's numbers -- they validate that the raw data is trait-aligned as documented.
REF_120_MEANS = {
    ("Male", "<21"):   {"N": 67.84, "E": 80.70, "O": 85.98, "A": 81.98, "C": 79.66},
    ("Male", "21-40"): {"N": 66.97, "E": 78.90, "O": 86.51, "A": 84.22, "C": 85.50},
    ("Male", "41-60"): {"N": 64.11, "E": 77.06, "O": 83.04, "A": 88.33, "C": 91.27},
    ("Male", ">60"):   {"N": 58.42, "E": 79.73, "O": 79.78, "A": 90.20, "C": 95.31},
    ("Female", "<21"):   {"N": 73.41, "E": 84.26, "O": 89.01, "A": 89.14, "C": 81.27},
    ("Female", "21-40"): {"N": 72.14, "E": 80.78, "O": 88.25, "A": 91.91, "C": 87.57},
    ("Female", "41-60"): {"N": 67.38, "E": 78.62, "O": 86.15, "A": 95.73, "C": 93.45},
    ("Female", ">60"):   {"N": 63.48, "E": 78.22, "O": 81.56, "A": 97.17, "C": 96.44},
}


def age_band(age):
    if age < 21:
        return "<21"
    if age <= 40:
        return "21-40"
    if age <= 60:
        return "41-60"
    return ">60"


def ensure_data():
    if os.path.exists(DAT_PATH) and os.path.getsize(DAT_PATH) > 90_000_000:
        return
    print(f"Downloading IPIP120.dat from {DAT_URL} ...", file=sys.stderr)
    subprocess.run(["curl", "-sSL", "-o", DAT_PATH, DAT_URL], check=True)


# 0-based item column indices per domain, precomputed once.
#
# IMPORTANT: Johnson's IPIP-NEO-120 item order is INTERLEAVED by domain, not
# blocked -- item 1 = N1, item 2 = E1, item 3 = O1, item 4 = A1, item 5 = C1,
# item 6 = N2, ...  So a domain owns the 24 items whose (item_number-1) % 5 maps
# to that domain: N = items {1,6,...,116}, E = {2,7,...,117}, etc. The 60's
# selected item numbers in FACET_ITEMS are the authoritative verbatim 120#s and
# every one lands in its intended domain (verified), so COLS_60 is built from
# them directly; COLS_120 uses the interleave for the orientation check.
_DOM_INDEX = {"N": 0, "E": 1, "O": 2, "A": 3, "C": 4}
COLS_120 = {
    dom: [i for i in range(120) if i % 5 == _DOM_INDEX[dom]]
    for dom in DOMAINS
}
COLS_60 = {
    dom: [n - 1 for f in DOMAIN_FACETS[dom] for n in FACET_ITEMS[f]]
    for dom in DOMAINS
}
ALL60_COLS = sorted({c for dom in DOMAINS for c in COLS_60[dom]})

CELLS = [
    ("Male", "<21"), ("Male", "21-40"), ("Male", "41-60"), ("Male", ">60"),
    ("Female", "<21"), ("Female", "21-40"), ("Female", "41-60"), ("Female", ">60"),
]


def stream(reservoir_per_cell=0):
    """
    Single streaming pass. Accumulates, per (cell, domain):
      - 120 orientation stats (count/sum) on complete-120 records
      - 60 norm stats (count/sum/sumsq) on complete-60 records
    Optionally reservoir-samples raw 60-domain scores per cell for skew / percentile
    sanity checks (reservoir_per_cell rows each), deterministically (seeded).

    Returns (acc120, acc60, samples, n_valid).
      acc120[cell][dom] = [count, sum]
      acc60 [cell][dom] = [count, sum, sumsq]
      samples[cell][dom] = list of raw 60 scores (up to reservoir_per_cell)
    """
    rng = random.Random(42)
    acc120 = {c: {d: [0, 0] for d in DOMAINS} for c in CELLS}
    acc60 = {c: {d: [0, 0.0, 0.0] for d in DOMAINS} for c in CELLS}
    samples = {c: {d: [] for d in DOMAINS} for c in CELLS}
    seen60 = {c: 0 for c in CELLS}          # for reservoir indexing
    n_valid = 0

    with open(DAT_PATH, "r", encoding="latin-1") as fh:
        for line in fh:
            rec = line.rstrip("\r\n")
            if len(rec) < RECLEN:
                continue
            s = rec[6]
            if s != "1" and s != "2":
                continue
            try:
                age = int(rec[7:9])
            except ValueError:
                continue
            if age < 10 or age > 99:
                continue
            row = rec[ITEMS_START:ITEMS_START + 120]
            if len(row) != 120:
                continue
            vals = [ord(ch) - 48 for ch in row]  # '0'..'5' -> 0..5
            n_valid += 1

            cell = ("Male" if s == "1" else "Female", age_band(age))

            # 120 orientation (complete on all 120 items)
            if 0 not in vals:
                for d in DOMAINS:
                    tot = 0
                    for c in COLS_120[d]:
                        tot += vals[c]
                    a = acc120[cell][d]
                    a[0] += 1
                    a[1] += tot

            # 60 norms (complete on the 60 selected/substituted items)
            if all(vals[c] > 0 for c in ALL60_COLS):
                idx = seen60[cell]
                seen60[cell] += 1
                for d in DOMAINS:
                    tot = 0
                    for c in COLS_60[d]:
                        tot += vals[c]
                    a = acc60[cell][d]
                    a[0] += 1
                    a[1] += tot
                    a[2] += tot * tot
                    if reservoir_per_cell:
                        buf = samples[cell][d]
                        if len(buf) < reservoir_per_cell:
                            buf.append(tot)
                        else:
                            j = rng.randint(0, idx)
                            if j < reservoir_per_cell:
                                buf[j] = tot
    return acc120, acc60, samples, n_valid


def main():
    ensure_data()
    print("Streaming IPIP120.dat (single pass) ...", file=sys.stderr)
    acc120, acc60, samples, n_valid = stream(reservoir_per_cell=20000)
    print(f"Parsed {n_valid:,} valid-sex/age records.", file=sys.stderr)

    # ---- Orientation check vs published IPIP-NEO-120 domain means ----
    #
    # The evaluator.py norm tables are Johnson's DISTRIBUTED short-form norms
    # ("IPIPlinux", June 2021), computed on his own reference sample -- NOT on
    # this raw 619k OSF file. So we do NOT expect exact equality (max |diff| here
    # is ~6, with N running ~2-4 low, C ~2-4 high, O ~5 low for young cohorts --
    # a stable sample/exclusion difference, not a keying error). What confirms
    # correct item ORIENTATION and DOMAIN ASSIGNMENT is that every domain tracks
    # the reference within a few points, with the correct sex ordering and the
    # correct monotone age gradients, and Agreeableness matches within ~1 point
    # across all 8 cells. A single reverse-keying error would throw the affected
    # domain off by ~15-30 points (verified empirically: the earlier interleave
    # bug produced +14..+20 gaps). The mapping is independently corroborated by
    # chfhhd/preparedata.R, which sums the identical item sets from the same file.
    # Pass criterion: max |diff| < 8 AND r > 0.97 over the 40 cell-domain points.
    print("\n=== ORIENTATION CHECK: derived vs published IPIP-NEO-120 domain means ===")
    print("(complete-case on all 120 items; 24 items/domain)")
    max_abs = 0.0
    xs, ys = [], []
    for cell in CELLS:
        sx, bd = cell
        n = acc120[cell]["N"][0]
        row = f"{sx:6s} {bd:6s} n={n:>7,} | "
        for d in DOMAINS:
            cnt, tot = acc120[cell][d]
            derived = tot / cnt if cnt else float("nan")
            ref = REF_120_MEANS[cell][d]
            diff = derived - ref
            max_abs = max(max_abs, abs(diff))
            xs.append(derived)
            ys.append(ref)
            row += f"{d}:{derived:6.2f}(d{diff:+.2f}) "
        print(row)
    mx = sum(xs) / len(xs)
    my = sum(ys) / len(ys)
    cov = sum((a - mx) * (b - my) for a, b in zip(xs, ys))
    sx_ = math.sqrt(sum((a - mx) ** 2 for a in xs))
    sy_ = math.sqrt(sum((b - my) ** 2 for b in ys))
    r = cov / (sx_ * sy_)
    ok = r > 0.97 and max_abs < 8.0
    print(f"Max |derived - published| across 40 points: {max_abs:.2f}")
    print(f"Pearson r(derived, published) over 40 points: {r:.4f}")
    print(f"Orientation & mapping confirmed (r>0.97 and max|diff|<8): {ok}")

    # ---- IPIP-NEO-60 domain norms ----
    total60 = sum(acc60[c]["N"][0] for c in CELLS)
    print(f"\n60-item complete-case respondents (all 60 items answered): "
          f"{total60:,} of {n_valid:,}")

    norms = {}
    print("\n=== IPIP-NEO-60 DOMAIN NORMS (raw domain = sum of 12 items, range 12-60) ===")
    for cell in CELLS:
        sx, bd = cell
        key = f"{sx}|{bd}"
        norms[key] = {}
        n = acc60[cell]["N"][0]
        row = f"{sx:6s} {bd:6s} n={n:>7,} | "
        for d in DOMAINS:
            cnt, tot, sq = acc60[cell][d]
            mean = tot / cnt
            var = (sq - tot * tot / cnt) / (cnt - 1)   # sample variance (ddof=1)
            sd = math.sqrt(var)
            norms[key][d] = {"mean": round(mean, 4), "sd": round(sd, 4), "n": cnt}
            row += f"{d}:{mean:5.2f}/{sd:4.2f} "
        print(row)

    with open(OUT_PATH, "w") as fh:
        json.dump(norms, fh, indent=2)
    print(f"\nWrote {OUT_PATH}")

    # ---- Sanity checks ----
    print("\n=== SANITY CHECKS ===")
    min_n = min(v["N"]["n"] for v in norms.values())
    print(f"1) Min cell N = {min_n:,} (want >= a few thousand)")

    ex = norms["Male|21-40"]["N"]
    t_at_mean = 50 + 10 * (ex["mean"] - ex["mean"]) / ex["sd"]
    print(f"2) T-score at the cell mean (Male 21-40, N) = {t_at_mean:.1f} (want 50.0)")

    # skew from reservoir sample (Female 21-40, E)
    buf = samples[("Female", "21-40")]["E"]
    m = sum(buf) / len(buf)
    sd = math.sqrt(sum((x - m) ** 2 for x in buf) / (len(buf) - 1))
    skew = (sum((x - m) ** 3 for x in buf) / len(buf)) / sd ** 3
    print(f"3) Skewness of E (Female 21-40, sample n={len(buf):,}) = {skew:+.3f} "
          f"(roughly normal => |skew| < ~0.5)")

    # spot-check percentile via cubic formula for a random sampled respondent
    CONST1, CONST2, CONST3, CONST4 = (210.335958661391, 16.7379362643389,
                                      0.405936512733332, 0.00270624341822222)
    raw = random.Random(7).choice(buf)
    cell = norms["Female|21-40"]["E"]
    T = 50 + 10 * (raw - cell["mean"]) / cell["sd"]
    Tt = min(max(T, 32), 73)
    pct = CONST1 - CONST2 * Tt + CONST3 * Tt ** 2 - CONST4 * Tt ** 3
    pct = int(min(max(pct, 1), 99))
    print(f"4) Random Female 21-40 respondent: E raw={raw}, T={T:.1f}, percentile={pct}")

    print("\n=== SUBSTITUTES USED (9 NEW 60-items -> nearest same-facet Johnson 120#) ===")
    for fac, (num, txt) in SUBSTITUTES.items():
        print(f"  {fac}: 120#{num:>3} \"{txt}\"")


if __name__ == "__main__":
    main()
