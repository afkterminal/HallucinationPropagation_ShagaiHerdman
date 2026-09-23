# Student A Research Plan — Propagation & Persistence Tracking

**Assigned to:** Shagai Herdman
**Project:** Hallucination Propagation in Iterative AI-Assisted Coding (4-student team)

This plan covers Student A's slice of the shared study: how hallucinations
move through multi-turn coding sessions, and which kinds survive longest. It
maps each assigned task to the code in this repository and states what is
automated and what still needs manual work. The original assignment notes are
in [SHAGAI_HERDMAN_PARTA.md](../SHAGAI_HERDMAN_PARTA.md).

## 1. Research questions and hypotheses

| | |
|---|---|
| **RQ1** | How do hallucinations propagate across iterative sessions (persist / mutate / disappear)? |
| **RQ2** | Which hallucination types are most likely to persist? |
| **H1** | Hallucinations persist across iterations unless explicitly identified and removed. |
| **H2** | Security hallucinations persist more than syntax hallucinations. |

**Focus:** longitudinal tracking of each hallucination's lifecycle across
iterations, grouped by type.

## 2. Data

| Source | Role |
|---|---|
| Shared trajectory corpus (built by the whole team) | Primary input: ≥ 5 logged refinement iterations per seed task |
| BigCodeBench, DS-1000 | Seed tasks. Library/API-heavy, so they provoke API and dependency hallucinations |
| EvalPlus (HumanEval+ / MBPP+) | Strong test suites to confirm a hallucination is truly resolved |
| Package-hallucination ("slopsquatting") name lists | Checked against live PyPI / npm registries to confirm fabricated dependencies |

**Labeling:** every hallucination gets a type (API / dependency / logic /
security / syntax), an iteration index, and a state, aligned with the
HalluCode / CodeHalu taxonomy. Confirm the current names, versions and
licenses of HalluCode and CodeHalu before committing to them. The
assignment notes this area changed quickly through 2025–2026.

## 3. Tasks and how they are implemented

| # | Assigned task | Where in the code | Status |
|---|---|---|---|
| 1 | Trace each hallucination's state across all iterations and label each transition | `IterationTestHarness.track_hallucination_propagation()` (automatic); `HallucinationTracker.load_annotations()` (manual labels) | Automatic detection distinguishes persist and resolve only. **Mutate must come from manual annotation** (see §4.2) |
| 2 | Persistence and mutation rate, overall and per type | `HallucinationTracker.compute_persistence_rate()`, `compute_mutation_rate()`, `persistence_by_type_df()`, `mutation_by_type_df()` | Implemented |
| 3 | Test H1 (with vs. without explicit "fix this" prompt) | `StatisticalAnalyzer.chi_square_test_h1()` + the `h1_counts()` helper in §5 | Implemented; needs corpus data |
| 4 | Test H2 (security vs. syntax persistence) | `HallucinationTracker.get_type_counts()` → `StatisticalAnalyzer.chi_square_test_h2()` | Implemented; needs corpus data |
| 5 | Propagation diagrams | `PropagationVisualizer` (persistence/mutation by type, severity, state-transition heatmap, dashboard) | Summary charts done. **Per-task flow diagram (iterations as columns) still to build** |

## 4. Method

### 4.1 Detection (per iteration)

`IterationTestHarness.add_iteration()` runs four checks on each iteration's code:

1. **Import analysis** — imported modules that cannot be found → *dependency*.
2. **Syntax check** — code that does not compile → *syntax*.
3. **Unit tests** — failures are grouped by their error message. A
   `NameError` for a real module → *dependency* (missing import); a
   `NameError` for anything else → *api* (invented function); all other
   failures → *logic*.
4. **Security pattern scan** — `eval`, `exec`, `pickle.loads`, `os.system`,
   `shell=True`, `__import__` → *security*.

Known limitations to address before the final analysis:

- The import check asks whether a module is installed **locally**, not
  whether it exists on PyPI. A real but uninstalled package is flagged as
  hallucinated. Slopsquatting candidates must be verified against the live
  registry.
- The security scan is a keyword match (so it also fires on comments and
  strings). Security results should come from Bandit/Semgrep, coordinated
  with Student C.

### 4.2 Lifecycle states

A hallucination is matched across iterations by its type plus its code
snippet or error message. Its final state is:

| State | Rule | Source |
|---|---|---|
| **resolve** | Not present in the latest iteration | Automatic |
| **persist** | Present in 2+ iterations, including the latest | Automatic |
| **new** | First seen in the latest iteration (no chance to be fixed yet) | Automatic |
| **mutate** | Same underlying error in a different form (e.g. a wrong import replaced by a different wrong import) | **Manual annotation** — automatic matching treats a changed snippet as a new hallucination |
| masked / compound | Looks fixed but tests fail / fix causes a new defect | Student B's analysis; the taxonomy supports them for shared labels |

Manual labels use the annotation format in
[SHAGAI_HERDMAN_PARTA.md](../SHAGAI_HERDMAN_PARTA.md) §1.2 plus a `state`
field, loaded with `HallucinationTracker.load_annotations_file()`.

### 4.3 Metrics

As implemented in [src/hallucination_tracker.py](../src/hallucination_tracker.py):

- **Persistence rate** = hallucinations present in 2+ iterations ÷ total unique hallucinations
- **Mutation rate** = persistent hallucinations with at least one *mutate* transition ÷ persistent hallucinations
- **Persistence duration** = last iteration present − first iteration present (0 = fixed in the next turn)

All three are computed overall and per type. Report persistence rates with
95% confidence intervals (e.g. Wilson intervals) in the final write-up; these
are not yet computed by the code.

## 5. Statistical tests

**H1 — explicit fix prompts.** Unit of analysis: each time a hallucination is
present at iteration *i* and iteration *i+1* exists. Group by whether the
prompt for *i+1* was an explicit fix prompt; count how often the
hallucination is still present at *i+1*.

```python
from src.statistical_tests import StatisticalAnalyzer

def h1_counts(reports):
    """Split every observed hallucination -> next-iteration step by whether the
    next prompt was an explicit fix prompt, and count how often it persisted."""
    groups = {
        True: {"count": 0, "persisting_count": 0},
        False: {"count": 0, "persisting_count": 0},
    }
    for report in reports:
        fix_prompt = {it["iteration"]: it["explicit_fix_prompt"] for it in report["iterations"]}
        for halluc in report["propagation_details"].values():
            seen = {inst["iteration"] for inst in halluc["instances"]}
            for i in seen:
                if i + 1 not in fix_prompt:
                    continue  # last iteration: nothing to observe afterwards
                group = groups[fix_prompt[i + 1]]
                group["count"] += 1
                group["persisting_count"] += (i + 1) in seen
    return groups[True], groups[False]

with_fix, without_fix = h1_counts(reports)   # reports = list of harness report dicts
h1 = StatisticalAnalyzer.chi_square_test_h1(with_fix, without_fix)
```

Note the key names: H1 expects `persisting_count`, H2 expects `persisting`.

**H2 — security vs. syntax.**

```python
counts = tracker.get_type_counts()
h2 = StatisticalAnalyzer.chi_square_test_h2(counts["security"], counts["syntax"])
```

**Sample size.** Chi-square is unreliable when any expected cell count is
below 5, and `scipy` raises an error when a whole row or column is zero
(this happens on the single-task pilot). If the corpus is small, use Fisher's
exact test (`scipy.stats.fisher_exact`) on the same 2×2 table and say so. The
assignment also allows a t-test for H2 (`StatisticalAnalyzer.t_test_mutation_rates`
compares per-task rates between two types).

## 6. Deliverables

1. Persistence and mutation rates per hallucination type, with confidence intervals
2. Propagation diagrams (summary charts plus per-task flow diagrams for ≥ 10 representative tasks)
3. H1 and H2 test results with p-values and effect sizes (Cramér's V)
4. Written answers to RQ1 and RQ2

Output files (from [SHAGAI_HERDMAN_PARTA.md](../SHAGAI_HERDMAN_PARTA.md)):
`persistence_rates.csv`, `mutation_rates.csv`, `state_transitions.csv`,
`propagation_diagrams/`, `survival_curves.png`, `statistical_results.json`.

## 7. Team dependencies

| Direction | What | With |
|---|---|---|
| Needs | The shared trajectory corpus and a common annotation format | Whole team |
| Shares | Security findings (H2 is reinforced by Student C's RQ4) | Student C |
| Feeds | Persistence rate and mutation rate per type → indicator validation | Student D |

Agree the export format for Student D early. `HallucinationTracker.export_results()`
writes the per-type rates and per-trajectory summaries as JSON.

## 8. Timeline

| Week | Work |
|---|---|
| 1 | Corpus setup with the team; pilot runs; annotation guideline |
| 2 | Finish annotations (including mutate labels); check data quality |
| 3 | Run tracking over the corpus; compute rates |
| 4 | H1/H2 tests; fix detection limitations (§4.1) |
| 5 | Propagation diagrams, survival curves, final report |

Progress is tracked in [RESEARCH_CHECKLIST.md](RESEARCH_CHECKLIST.md).
