# Quick Start

Get the Student A pipeline running on your machine in about five minutes:
install, run the example session, then compute metrics and charts from it.

## 1. Install

You need Python 3.10 or newer.

```bash
git clone https://github.com/afkterminal/HallucinationPropagation_ShagaiHerdman.git
cd HallucinationPropagation_ShagaiHerdman
python -m pip install -r requirements.txt
```

This installs numpy, pandas, scipy and matplotlib. If you will generate new
trajectories with an LLM, also run `python -m pip install anthropic` (see
[LLM_INTEGRATION.md](LLM_INTEGRATION.md)).

## 2. Run the example session

```bash
python examples/example_test_run.py
```

The script feeds five hand-written iterations of a JSON-parsing task through
the test harness. You should see two hallucinations detected:

| Hallucination | Type | Appears in | Final state |
|---|---|---|---|
| `NameError: name 'json' is not defined` (missing import) | dependency | iteration 0 | resolve |
| `NameError: name 'validate_email' is not defined` (invented helper) | api | iteration 3 | resolve |

The full log is written to `test_outputs/test_report_json_parser_task.json`.
That folder is ignored by git, so rerunning is safe.

## 3. Analyze the report

Save this as `analyze.py` in the repository root and run `python analyze.py`:

```python
import json

from src.hallucination_tracker import HallucinationTracker
from src.propagation_visualizer import PropagationVisualizer

with open("test_outputs/test_report_json_parser_task.json", encoding="utf-8") as f:
    report = json.load(f)

tracker = HallucinationTracker("pilot")
tracker.load_harness_report(report)   # call once per task report

print(tracker.get_summary_stats())
print(tracker.persistence_by_type_df())

viz = PropagationVisualizer("outputs")
viz.plot_persistence_by_type(tracker.persistence_by_type_df(), "outputs/persistence_by_type.png")
viz.create_summary_dashboard(tracker.get_summary_stats(), "outputs/summary.png")
tracker.export_results("outputs/results.json")
```

Charts and `results.json` land in `outputs/` (also ignored by git).

## 4. What each module does

| File | Role |
|---|---|
| [src/test_harness.py](../src/test_harness.py) | `IterationTestHarness` — logs each iteration, runs the unit tests, detects hallucinations (imports, syntax, test failures, basic security patterns) and writes a per-task JSON report. |
| [src/hallucination_taxonomy.py](../src/hallucination_taxonomy.py) | Types (api, dependency, logic, security, syntax, …), states (persist, mutate, resolve, masked, compound) and severities. |
| [src/hallucination_tracker.py](../src/hallucination_tracker.py) | `HallucinationTracker` — loads harness reports or manual annotations and computes persistence, mutation and duration metrics. |
| [src/statistical_tests.py](../src/statistical_tests.py) | `StatisticalAnalyzer` — chi-square tests for H1 and H2, t-test and duration summaries. |
| [src/propagation_visualizer.py](../src/propagation_visualizer.py) | `PropagationVisualizer` — bar charts, state-transition heatmap and summary dashboard. |

## 5. Common problems

- **`ModuleNotFoundError: No module named 'src'`** — run scripts from the
  repository root, not from inside `src/` or `examples/`.
- **`ModuleNotFoundError: No module named 'pandas'`** — step 1 was skipped, or
  VS Code is using a different Python. Pick the interpreter with
  *Python: Select Interpreter* and reinstall.
- **`ValueError: ... expected frequencies has a zero element`** from a
  chi-square test — one group has no observations yet. You need more tasks
  before H1/H2 can be tested; see
  [STUDENT_A_RESEARCH_PLAN.md](STUDENT_A_RESEARCH_PLAN.md#5-statistical-tests).

Next: [LLM_INTEGRATION.md](LLM_INTEGRATION.md) to generate real trajectories,
and [RESEARCH_CHECKLIST.md](RESEARCH_CHECKLIST.md) to track progress.
