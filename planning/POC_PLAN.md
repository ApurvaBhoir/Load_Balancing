# Proof of Concept Plan – Production Load Balancing Decision Support Tool

## A. Vision: Empowering Planners with Data-Driven Decisions

### The Current Challenge
- **Manual Planning**: Planners rely on experience and educated guesses to schedule production
- **Suboptimal Results**: Heavy Mon-Wed loads, light Thu-Fri, overtime costs, employee stress
- **Limited Support**: No tools to systematically forecast workload or optimize distribution

### Our Solution
A decision support tool that transforms the planner's workflow:
1. **Input**: Planner enters manager-defined requirements + constraints
2. **Process**: System forecasts load distribution and optimizes schedule
3. **Output**: Balanced weekly plan with clear rationale and compliance indicators

### Success Proof Points
- Demonstrate 15%+ reduction in daily load variance
- Show constraint compliance with transparent reasoning
- Provide actionable weekly schedules planners can actually use

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

### Deliverables (demo‑ready planner tool)
- **Planner Interface**: Web form where planners can input production requirements and constraints
- **Forecasting Engine**: System that predicts load distribution based on historical patterns
- **Optimization Engine**: Scheduler that balances load while respecting all constraints
- **Output Dashboard**: Clear weekly schedule with:
  - Hours per weekday (stacked by line)
  - Load distribution metrics and trends
  - Constraint compliance indicators (pass/fail badges)
  - Rationale for scheduling decisions
- **Export Capability**: Download optimized schedule as CSV/Excel for implementation

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

### 14‑day execution plan (planner-focused development)

#### Phase 1: Foundation (Days 1-4)
- **Days 1-2**: Data pipeline - parse Excel files, normalize schema, validate quality
- **Days 3-4**: Baseline analysis - understand patterns, constraints, and planner needs

#### Phase 2: Core Intelligence (Days 5-8)
- **Days 5-6**: Forecasting engine - build load prediction model based on historical data
- **Days 7-8**: Optimization engine - implement constraint-aware scheduling algorithm

#### Phase 3: Planner Interface (Days 9-12)
- **Days 9-10**: Input forms - create web interface for requirements and constraints
- **Days 11-12**: Output dashboard - build schedule visualization and export features

#### Phase 4: Integration & Demo (Days 13-14)
- **Day 13**: End-to-end testing - validate complete planner workflow
- **Day 14**: Demo preparation - polish interface, prepare stakeholder presentation

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

### Expected Outputs (14-day deliverables)
- **Working Planner Interface**: Web application where planners can input requirements and get optimized schedules
- **Demonstration Scenarios**: 2-3 historical weeks showing "manual vs. optimized" comparisons
- **Technical Documentation**: Setup guides, user manuals, and API documentation
- **Business Case**: Quantified benefits - overtime reduction, load smoothing, constraint compliance
- **Stakeholder Demo**: End-to-end workflow demonstration for management and planning teams

### Success Validation
- **User Experience**: Planners can complete the full workflow (input → forecast → optimize → export) in <5 minutes
- **Technical Performance**: System generates optimized schedules in <30 seconds
- **Business Impact**: Demonstrate 15%+ reduction in daily load variance while maintaining 100% constraint compliance
- **Adoption Readiness**: Clear path to production deployment with documented requirements and technical architecture
