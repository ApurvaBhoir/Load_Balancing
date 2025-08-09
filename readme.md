# Ritter Sport – Production Load Balancing (Master README)

This repository consolidates data, findings, constraints, and the working plan for optimizing weekly load balancing across Ritter Sport’s production lines. It is the single source of truth for the project.

### What this is about
- **Goal**: Smooth weekly production load, reduce overtime and idle time, and improve planner experience.
- **Scope**: 5 production lines (Anlagen) across Hohl and Massiv, 3 shifts/day, weekly planning horizon.
- **Focus**: Use historical data to forecast near-term workload and optimize the allocation of lines and shifts under real-world constraints.


## 1) Problem, Objectives, and Success Criteria

- Production is highly loaded on Mon–Wed with steep drop-off Thu–Fri leading to overtime and end-of-week idle time.
- Several line clusters are bottlenecks (e.g., hohl 3, massiv 3) while others (e.g., hohl 4) are underutilized.

Objectives
- Balance load across Mon–Fri so average lines active and total hours are steadier.
- Respect operational, product, and staffing constraints (see Constraints).
- Provide a decision-support tool that produces a weekly plan (3 shifts/day) with minimal disruptions.

Target benefits (from pitch)
- ≈ 20% fewer overtime hours; ≈ 15% less idle time in pilot.
- Smoother energy demand curve; more transparent planning process.

KPIs
- Overtime hours, idle variance across the week, number of active lines per day, plan stability (few changes), planner satisfaction.


## 2) Data Overview and Layout

Folder structure
- `2024/` and `2025/` contain week-level Excel files grouped by area:
  - `H2_H3/` (Hohl 2 & 3), `H4/` (Hohl 4), `M2_M3/` (Massiv 2 & 3)
  - Files come in two variants per KW (calendar week):
    - `Konzept` → initial 2-week plan (first week mostly reliable; second week more uncertain)
    - `Version 1` → realized/implemented plan (ground truth)

Observed columns (notes)
- Date/time, `start`, `end`, `min` (tbd), `soll` (planned workload), `Rezeptur` (recipe/product config), `product` (chocolate type).

Glossary of lines (as used in analysis)
- `hohl2`, `hohl3`, `hohl4`, `massiv2`, `massiv3`.

How to add new data
- Place new weekly Excel files under the correct year and area subfolder.
- Favor including both `Konzept` and `Version 1` where available.
- Keep file names consistent: `WP_<AREA>_KW <week> <suffix>.xlsx`.
- Document any schema changes (new columns, renamed headers) in this README.


## 3) Constraints and Planning Rules

From `rahmenbedingungen.md` (original German retained where specific):
- Mindestens eine Anlage steht (not all 5 run simultaneously at all times).
- Keine gleichzeitige Produktion personalintensiver Sorten:
  - 100g Knusperkeks, 100g Waffel, 100g Marzipan, Mini Knusperkeks, SW (Schokowürfel).
- 3‑Schicht‑Modell wird beibehalten (Ausnahme Massiv 2 möglich).
- Max 1 Unterbrechung des Produktionsblocks während der Woche.
- Unterbrechung von Produktionsblöcken bevorzugt an Massivanlagen.
- Keine Unterbrechung von Sortenblöcken bei Hohl‑Anlagen.
- Zusatz (aus `notes.md`): Nicht dieselbe Sorte am Tag und am Folgetag produzieren.

Planning granularity
- Weekly horizon, 3 shifts/day, all 5 lines available, lines can produce any sort (with above constraints on combinations/sequencing).


## 4) Exploratory Findings (Current State)

Based on `production-analysis.html` (8 weeks sample):
- Average total hours per weekday (approx.):
  - Mon ≈ 236 h, Tue ≈ 280 h, Wed ≈ 230 h, Thu ≈ 149 h, Fri ≈ 37 h.
  - Avg active lines: Mon ~4.3, Tue ~4.6, Wed ~4.3, Thu ~3.0, Fri ~1.4.
- Increasing total weekly hours from KW28→KW35 (558 h → 1,370 h) without resolving front‑loaded pattern.
- Line contributions: `massiv3` and `hohl3` bear the highest loads; `hohl4` contributes the least in the observed sample.

How to view the analysis
- Open `production-analysis.html` in a browser. It includes:
  - Avg total production by weekday
  - Daily stacked utilization across the 5 lines
  - Weekly totals and line breakdowns
  - Personnel load (max/avg/min by weekday) and average active lines
  - Per-line total hours and active-day counts


## 5) Methodology (Forecast + Optimization)

Forecasting (near-term workload per line/day)
- Primary: Gradient Boosting (LightGBM / XGBoost)
- Fallback: N‑BEATS or TFT (Temporal Fusion Transformer) for complex patterns / multi-horizon
- Feature engineering: lags (T‑1, T‑7), rolling stats, calendar/holiday flags, recipe/sort indicators, area (Hohl vs Massiv)
- Validation: Walk-forward backtesting, MAPE/RMSE

Optimization (weekly schedule under constraints)
- Primary: Reinforcement Learning (online in a digital twin or offline on logs)
  - Env: Gym-compatible simulator of lines, shifts, constraints
  - Reward (penalize): line idle hours, unused worker hours, peak loads, constraint breaches
  - Output: 3‑shift plan for Mon–Fri across 5 lines respecting constraints
- Alternative/Hybrid: MILP via OR‑Tools/Pyomo for baseline or constraint-hardening

Key artifacts (from pitch)
- Deliverables: cleaned dataset + feature store; trained forecast model; scheduling engine (Python package) + REST/Excel interface; dashboard (Dash/Streamlit); final report w/ business case
- Timeline (24 weeks, Mar–Aug 2026):
  - W1–4 Data & EDA; W5–8 Forecast; W9–14 Optimization; W15–18 UI Pilot; W19–22 Evaluation; W23–24 Write‑up

Evaluation
- Forecast: MAPE, RMSE
- Scheduling: reduction in overtime, variance in daily totals/active lines, plan stability, planner satisfaction
- A/B tests on historical weeks (simulate vs realized), pilot with planning team


## 6) Working Agreements and Assumptions

- Weekly plan with 3 shifts/day returned by the optimizer (exception logic for Massiv 2 where applicable).
- Lines can produce all sorts; constraints govern simultaneous sorts and sequencing.
- Not producing identical sort on consecutive days on the same line.
- Max one interruption per production block/week; prefer interruptions on Massiv, avoid splitting sort blocks on Hohl.
- At least one line can be planned idle to accommodate staffing/cleaning/maintenance.


## 7) Practical Usage (Today and Next)

Today
- Data lives in `2024/` and `2025/` folders; open `production-analysis.html` for the current visual EDA.
- Planning constraints are captured in `rahmenbedingungen.md` and above.

Next steps (implementation outline)
1) Data ingestion & schema unification
- Build parsers for `Konzept` and `Version 1` Excel schemas; normalize to a common table: date, line, shift, product/sort, start, end, minutes, planned (`soll`), realized, recipe
- Add validators (empty cells, time overlaps, line/day totals)

2) Forecasting pipeline
- Feature store; backtesting; model registry w/ Optuna tuning
- Output daily/shift-level workload per line with uncertainty bounds

3) Scheduling engine
- Gym env for weekly schedule; encode constraints; baseline MILP; then RL with well-shaped reward
- Export plan to Excel/CSV + visualization dashboard

4) Dashboard
- Provide weekly overview (by weekday, by line), deltas vs current plan, constraint flags, what-if toggles

5) Ops & governance
- Logging/telemetry, reproducible runs, versioned data and models (MLflow/Weights & Biases)


## 8) Repository Guide

Key documents
- `notes.md` → plain-language problem statement and initial requirements
- `rahmenbedingungen.md` → constraints to encode in the optimizer
- `production-analysis.html` → current visual analysis of 8 weeks sample
- `Pitch_and_details.md` → project pitch, methods, deliverables, and timeline
- `Notes/` → miscellaneous notes (some are unrelated, e.g., amberSearch, ticket dispatcher)

Planned structure (to be added as code is implemented)
- `src/etl/` → Excel parsers, normalization, validation
- `src/features/` → Feature engineering for forecasting
- `src/forecast/` → Models (LightGBM/XGBoost, N‑BEATS/TFT), backtesting
- `src/scheduler/` → MILP baseline + RL Gym env, policies
- `dashboards/` → Dash/Streamlit apps, static `production-analysis.html`
- `data/` → Optional curated data exports (parquet/csv) derived from `2024/` and `2025/`


## 9) Open Questions (to resolve before productionization)
- Column semantics and units: confirm `min`, `soll`, and any hidden business rules.
- Exact definition of “personnel‑intensive” sorts; full list and maintainability of the list.
- Cleaning/maintenance windows and mandatory changeover times between certain sorts.
- Massiv 2 exception: what deviations from the 3‑shift model are allowed/typical?
- Objective weighting in the optimizer (idle vs overtime vs plan stability vs energy cost).
- Output format preferred by planners (Excel template? REST? Scheduling signals to MES?).


## 10) Getting Started (Short)
- Clone or open this repo.
- Review constraints in this README and in `rahmenbedingungen.md`.
- Open `production-analysis.html` in your browser.
- When implementation begins, start with ETL for Excel files under `2024/` and `2025/` and align a single normalized schema.


---

Maintainers: Planning & AI Team
Last updated: 2025-08-08
