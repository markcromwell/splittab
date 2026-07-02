# Program Map: SplitTab

<!--GENERATED:BEGIN hash=8bf68d8f75902413e96f52f9c6d08138642763867fbd5aac6a1c76644ed0277c sig= job=0 commit=37d2f11ad562ea57410ca745169bf26d8d348ebd-->
<!--Generated 2026-07-02T13:26:00.882244+00:00. Do not edit — will be overwritten.-->

## II. Canonical Data Schema [GENERATED — do not edit]

_No SQLAlchemy models found._

## III. File and Module Map [GENERATED — do not edit]

```
.dockerignore
.env.example
.github/workflows/ci.yml
.gitignore
Dockerfile
PROGRAM_MAP.md
README.md
app/__init__.py
app/config.py
app/health.py
app/routers/__init__.py
app/routers/root.py
app/routers/split.py
app/split_core.py
docker-compose.yml
main.py
pyproject.toml
requirements.in
requirements.lock
scripts/__init__.py
scripts/setup.py
scripts/smoke_boot.py
scripts/test_unit.py
```

## IV. API Surface [GENERATED — do not edit]

| Method | Path | Status Code |
|--------|------|-------------|
| GET | `/` | 200 |
| GET | `/health` | 200 |
| POST | `/split` | 200 |

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
