# Big Five App

A web app where a person takes an IPIP-NEO Big Five personality test with Gallup-style mechanics
(soft per-item timer, continuous slider), receives a plain-language report, and can talk to an AI
coach seeded with their results.

## Language

**Profile**:
The identity everything hangs off — issued as an opaque ID on first visit (anonymous), later claimable by an Account.
_Avoid_: user, session

**Account**:
A Clerk-managed sign-in that claims exactly one Profile; required to create a Coach, not to take the test or read a Report.
_Avoid_: user (ambiguous), login

**Form**:
One of the two published test lengths — Quick (IPIP-NEO-60) or Full (IPIP-NEO-120).
_Avoid_: version, mode, test type

**Item**:
A single statement the person rates ("I am the life of the party."), carrying its domain, facet, and keying.
_Avoid_: question (UI copy may say "Question 12 of 60", but code and docs say Item)

**Test Run**:
One attempt at a Form by a Profile, from first Item to scoring; answers are one-shot (no revisiting, see ADR-0001); exiting mid-run abandons it.
_Avoid_: session, attempt, quiz

**Answer**:
The committed slider value (1–5 scale) for one Item in a Test Run — committed by Next or by timer expiry (untouched slider = Neutral), never revised.
_Avoid_: response (reference-repo term), rating

**Score**:
A percentile (1–99) against the age/sex norm group, shown as the 0–100 bar values in the report; computed per domain and, on the Full form, per facet.
_Avoid_: raw score (the 1–5 sums — internal only), T-score (internal intermediate)

**Report**:
The rendered result of a completed Test Run: five domain Scores plus narrative (pull-quote, "Who you are", strengths, watch-outs), downloadable as PDF.
_Avoid_: results (the stale codebase's term)

**Coach**:
The per-Profile AI companion (default name "Sol"), seeded with the latest completed Test Run's Scores; chat history survives retakes.
_Avoid_: chatbot, assistant

## Relationships

- A **Profile** owns many **Test Runs**; each completed Test Run yields one **Report**.
- An **Account** claims exactly one **Profile** (at Coach creation); a Profile without an Account can test and read Reports but has no Coach.
- A **Profile** has at most one **Coach**; the Coach's trait context always reflects the latest completed **Test Run**.
- A **Test Run** has exactly one **Form** and one **Answer** per **Item** of that Form.

## Example dialogue

> **Dev:** "If a **Profile** retakes the **Full Form**, does the **Coach** get a second set of **Scores**?"
> **Domain expert:** "The **Coach** always speaks from the latest completed **Test Run** — it may acknowledge the change, but there is one trait context, not an archive."
> **Dev:** "And if the timer fires before the person touches the slider?"
> **Domain expert:** "That commits a Neutral **Answer** — a **Test Run** never has gaps and an **Answer** is never revised."

## Flagged ambiguities

- "account" — originally deferred, later pulled into v1 (Clerk) when retake/persistence semantics were grilled; resolved: **Account** is only a claim on a **Profile**, all data stays keyed by Profile.
- "score" was used for raw sums, T-scores, and percentiles interchangeably in the reference repo — resolved: **Score** means the percentile a user sees; the others are internal terms.
- "Save & exit" (wireframe copy) — resolved: there is no saving; the link is relabelled "Exit test" and exiting abandons the **Test Run**.
