# Proof of Concept Plan – Production Load Balancing at Ritter Sport

## A. Intuitive outline (how this can work)
- Understand the problem: Today most hours happen Mon–Wed; Thu–Fri are quiet. Some lines are overloaded, others underused.
- Predict next week’s need: From recent weeks, estimate how many hours each line will likely need on each weekday.
- Propose a smoother plan: Spread those hours more evenly across Mon–Fri while respecting key rules (3 shifts/day, at least one line idle, no simultaneous personnel‑intensive sorts).
- Show the impact: Compare “current vs proposed” on a few simple charts (hours/day, active lines/day, overtime/idle proxies) to prove smoothing is possible without breaking rules.

## B. Two‑week Proof‑of‑Concept plan (minimal, end‑to‑end)

### Scope (kept small on purpose)
- Data: Use 8–12 historical weeks already summarized in `production-analysis.html` (e.g., KW28–35) and a handful of raw Excel files from `2024/` and `2025/` for spot checks.
- Constraints (POC subset):
  - 3 shifts/day; 5 lines available.
  - At least one line idle per day.
  - No simultaneous personnel‑intensive sorts (list from `rahmenbedingungen.md`).
- Output: A 1‑week schedule suggestion that’s smoother than the baseline, plus a tiny dashboard to visualize before/after.

### Success criteria (binary, POC-level)
- Reduce the Mon–Tue peak vs. Thu–Fri trough by ≥15% (variance of daily totals).
- Keep average active lines/day near 4 on Mon–Wed and ≥3 on Thu–Fri (no Friday collapse).
- Satisfy the three POC constraints above on all days.

### Deliverables (simple and demo‑ready)
- One suggested weekly plan (CSV/Excel) with per‑day, per‑line hours and shift split.
- A lightweight dashboard (Streamlit or static HTML) showing before/after:
  - Hours per weekday (stacked by line)
  - Average active lines per day
  - Constraint flags (pass/fail)
- A 1‑page note with metrics: baseline vs. proposed.

### Minimal technical approach
- Data ingestion (light)
  - Parse a small sample of weekly Excel files from `2024/` and `2025/` to confirm columns (date, start, end, minutes, `soll`, product, line).
  - Create a tiny normalizer that outputs a simple table: day, line, total_hours.
  - If sort mapping is messy, tag “personnel‑intensive” sorts with a simple keyword list; otherwise apply a simplified check (max 1 such tag/day).
- Forecast (fast baseline)
  - Baseline: rolling average hours by weekday per line (last 4–8 weeks).
  - Optional (time permitting): LightGBM with calendar features to refine the weekday signal.
- Scheduling (simple but convincing)
  - Start with a greedy smoother:
    - For each day, target “total hours/day” = weekly sum / 5.
    - Allocate line hours to get close to the target, keeping at least 1 line idle.
    - Enforce “no simultaneous personnel‑intensive sorts” by moving one line’s hours to another day if needed.
  - Optional baseline MILP (small model) if we need stronger guarantees:
    - Variables: hours(line, day). Objective: minimize day‑to‑day deviation from target.
    - Constraints: capacity per line/day, at least one line idle, personnel‑intensive conflict.
- Visualization
  - Reuse the look/feel of `production-analysis.html`:
    - Stacked daily bars (lines as stacks).
    - A small table of constraint checks.
    - A single KPI row (var(day totals), avg active lines/day).

### 10‑day execution plan (2 weeks)
- Days 1–2: Confirm columns on 3–5 files. Build normalizer to produce day×line hours. Draft the personnel‑intensive keyword list.
- Days 3–4: Baseline forecast (weekday averages). Sanity charts vs. history.
- Days 5–6: Greedy smoothing prototype; ensure 3 constraints pass; auto‑export plan CSV.
- Days 7–8: Mini‑dashboard (Streamlit or static HTML) with before/after charts and pass/fail badges.
- Day 9: Polish: small MILP alternative (optional) OR strengthen greedy edge cases.
- Day 10: Freeze demo: pick 1–2 historical weeks; produce “current vs proposed”; finalize KPI summary.

### Risks and simple mitigations
- Messy product/sort tags: fallback to a conservative conflict rule (limit number of personnel‑intensive allocations per day).
- Column ambiguities (`min`, `soll`): for POC, rely on computed `end-start` or trusted columns in sampled weeks; document ambiguity.
- Friday underflow persists: bias the smoother’s target to lift Thu–Fri (slight weight in objective).

### What this proves (decision point)
- There is clear, quantifiable headroom to flatten the weekly curve without violating basic rules.
- Minimal architecture (simple forecast + simple optimizer) already yields visible improvements, justifying full build‑out (better data model, richer constraints, RL/MILP hybrid, dashboard).

### What comes after (if green‑lit)
- Broaden data coverage and formalize product/recipe constraints.
- Replace weekday‑average forecast with tuned LightGBM/TFT.
- Upgrade scheduler to MILP + RL simulation, add “no same sort on consecutive days” robustly.
- Integrate planner UI and Excel/REST outputs.

### Inputs this plan used
- Constraints from `rahmenbedingungen.md`
- Problem and aims from `notes.md` and `Pitch_and_details.md`
- Patterns from `production-analysis.html`

### Outputs you’ll see in 2 weeks
- `proposed_schedule_week_X.csv` (one week)
- `poc_dashboard` (Streamlit app or `poc_analysis.html`)
- `poc_summary.pdf` or `poc_summary.md` with KPI deltas

### Decisions needed now
- Which weeks to test (suggest KW28–35) and one target week for the “proposal.”
- Confirm the personnel‑intensive sort list and a basic name matching rule.
