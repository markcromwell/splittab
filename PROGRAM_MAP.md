# Program Map: SplitTab

<!--GENERATED:BEGIN hash=UNINITIALIZED-->
<!--This map is maintained automatically by Code Forge.-->
<!--Sections II, III, IV are generated from AST after each successful merge.-->
<!--Do not edit sections II, III, IV manually — they will be overwritten.-->

## I. Implementation Status [CURATED]
SplitTab MVP is implemented as a standalone FastAPI service with:
- `GET /health` returning `{"status": "ok"}`.
- `POST /split` accepting subtotal, people, tip percentage, and tax inputs.
- Pure integer-cent split computation in `app.split_core`.

---

## II. Canonical Data Schema [GENERATED — do not edit]
_No models detected yet._

---

## III. File and Module Map [GENERATED — do not edit]
_Will be populated after first merge._

---

## IV. API Surface [GENERATED — do not edit]
_No routes detected yet._

<!--GENERATED:END-->

---

## V. Architectural Decisions [CURATED]
### ADR: SplitTab tip rounding and cent distribution

Tip cents are rounded with the HALF-UP convention: compute
`subtotal_cents * tip_pct / 100`, then round fractional cents so `.5` rounds up
to the next cent. The charged total is always
`subtotal_cents + rounded_tip_cents + tax_cents`.

Splits must preserve the hard invariant
`sum(per_person) == total_charged_cents`. The service computes
`base = total_charged_cents // people` and `rem = total_charged_cents % people`;
the first `rem` people pay `base + 1`, and the remaining people pay `base`.

---

## VI. Planned Work [CURATED]
_To be populated by the spec planner._
