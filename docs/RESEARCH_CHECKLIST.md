# Research Checklist — Student A

Tick items off as they are completed. Items already done in this repository
are checked. Details for each phase are in
[STUDENT_A_RESEARCH_PLAN.md](STUDENT_A_RESEARCH_PLAN.md).

## Phase 0 — Tooling

- [x] Test harness logs iterations, runs unit tests, detects hallucinations
- [x] Taxonomy of types, states and severities
- [x] Tracker computes persistence, mutation and duration metrics
- [x] H1 and H2 chi-square tests
- [x] Summary charts (persistence/mutation by type, severity, transition heatmap, dashboard)
- [x] Example session runs end to end (`python examples/example_test_run.py`)
- [ ] Per-task propagation flow diagram (iterations as columns, hallucinations as color-coded nodes)
- [ ] Survival curve (% of hallucinations still present at each iteration)
- [ ] 95% confidence intervals for persistence and mutation rates
- [ ] Fisher's exact test fallback for small samples

## Phase 1 — Data (with the team)

- [ ] Confirm current names, versions and licenses of HalluCode, CodeHalu (and CyberSecEval with Student C)
- [ ] Agree the multi-turn harness (InterCode or MINT) and trajectory JSON format
- [ ] Select seed tasks: BigCodeBench, DS-1000, EvalPlus (prefer LiveCodeBench tasks where contamination is a concern)
- [ ] Randomly assign each task to the explicit-fix or control condition (fixed seed)
- [ ] Record model ID, run date and harness settings in corpus metadata
- [ ] Pilot run on 3–5 tasks; check cost and that reports load into the tracker
- [ ] Full run: 50–100 tasks × ≥ 5 iterations
- [ ] Log refusals and failed runs; decide exclusion rules before analysis

## Phase 2 — Annotation

- [ ] Write the annotation guideline (type, iteration, state, severity; HalluCode/CodeHalu aligned)
- [ ] Label *mutate* transitions manually (not detected automatically)
- [ ] Double-annotate a sample and report inter-annotator agreement (Cohen's κ)
- [ ] Verify fabricated packages against live PyPI / npm (slopsquatting lists)
- [ ] Run Bandit/Semgrep on every iteration; replace keyword-based security labels (coordinate with Student C)
- [ ] Confirm resolved hallucinations against EvalPlus tests

## Phase 3 — Analysis

- [ ] Persistence rate, overall and per type (RQ1, RQ2)
- [ ] Mutation rate, overall and per type
- [ ] Persistence duration distribution per type
- [ ] State-transition matrix
- [ ] H1: explicit fix prompt vs. control (chi-square, or Fisher's exact if expected counts < 5)
- [ ] H2: security vs. syntax persistence
- [ ] Effect sizes (Cramér's V) reported with every p-value

## Phase 4 — Deliverables

- [ ] `persistence_rates.csv` and `mutation_rates.csv`
- [ ] `state_transitions.csv`
- [ ] Propagation diagrams for ≥ 10 representative tasks
- [ ] `survival_curves.png`
- [ ] `statistical_results.json`
- [ ] Per-type rates exported to Student D in the agreed format
- [ ] Written answers to RQ1 and RQ2, with limitations (detection heuristics, sample size, single model)

## Success criteria

- [ ] ≥ 50 tasks with ≥ 5 iterations each
- [ ] Persistence and mutation rates with confidence intervals
- [ ] H1 and H2 tested, p-values and effect sizes reported
- [ ] ≥ 10 propagation diagrams
- [ ] Clear answers to RQ1 and RQ2
