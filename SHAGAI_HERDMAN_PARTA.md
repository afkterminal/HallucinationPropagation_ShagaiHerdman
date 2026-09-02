# Student A Research Implementation - Hallucination Propagation & Persistence Tracking

**Research Questions:**
- RQ1: How do hallucinations propagate across iterative sessions (persist / mutate / disappear)?
- RQ2: Which hallucination types are most likely to persist?

**Hypotheses:**
- H1: Hallucinations persist across iterations unless explicitly identified and removed
- H2: Security hallucinations persist more than syntax hallucinations

---

## Phase 1: Data Preparation (Weeks 1-2)

### 1.1 Build the Shared Corpus
Work with team to create logged trajectories using **InterCode** or **MINT**:
- Run 50-100 seed tasks from BigCodeBench, DS-1000, and EvalPlus
- Generate ≥5 refinement iterations per task
- Log every LLM output, test results, and state changes
- Save as: `corpus/trajectories_{task_id}.json`

Example trajectory structure:
```json
{
  "task_id": "bigcodebench_001",
  "seed_prompt": "Write a function to parse JSON safely",
  "iterations": [
    {
      "iteration": 0,
      "llm_output": "def parse_json(s):\n  return json.loads(s)",
      "tests_passed": 2,
      "tests_failed": 3,
      "test_output": "ImportError: No module named 'json'",
      "hallucinations_detected": ["api_missing_import"]
    },
    {
      "iteration": 1,
      "llm_output": "import json\ndef parse_json(s):\n  return json.loads(s)",
      "tests_passed": 5,
      "tests_failed": 0,
      "hallucinations_detected": []
    }
  ]
}
```

### 1.2 Manual Hallucination Annotation
For each iteration with failures or security issues:
- Identify and label each hallucination
- Record: type, location, severity, how it was detected
- Track what changed between iterations

Annotation template:
```json
{
  "hallucination_id": "h_001_api_missing",
  "task_id": "bigcodebench_001",
  "iteration": 0,
  "type": "api",
  "code_snippet": "return json.loads(s)",
  "description": "Missing 'import json' statement",
  "severity": "critical",
  "location": "line 1",
  "detected_by": "ImportError at runtime"
}
```

---

## Phase 2: Core Analysis (Weeks 3-4)

### 2.1 Trace Hallucination Lifecycles
For each hallucination across all iterations, determine:
- **PERSIST**: Same hallucination appears in next iteration unchanged
- **MUTATE**: Hallucination changes form but same underlying error persists
- **RESOLVE**: Hallucination is fixed/removed
- **MASKED**: Appears fixed but tests still fail
- **COMPOUND**: Causes new defect to emerge

Example lifecycle:
```
Iteration 0: "import json" missing → PERSIST
Iteration 1: "import json" still missing → PERSIST
Iteration 2: "import json" added, but wrong import statement → MUTATE
Iteration 3: Correct import, all tests pass → RESOLVE
```

### 2.2 Calculate Persistence Metrics
For all hallucinations:
- **Persistence rate** = (hallucinations appearing in 2+ iterations) / (total unique hallucinations)
- **Mutation rate** = (hallucinations that change form) / (persistent hallucinations)
- **Persistence duration** = average number of iterations a hallucination survives

Per hallucination type:
- Compute same metrics grouped by: API, dependency, logic, security, syntax

### 2.3 Statistical Validation

**Test H1:** Explicit fix prompts reduce persistence
- Split data: iterations WITH "fix this" prompt vs. WITHOUT
- Chi-square test: persistence rate differs significantly?
- Expected: With fix prompt → lower persistence

**Test H2:** Security hallucinations persist more than syntax
- Compare security vs. syntax persistence rates
- Chi-square test: significant difference?
- Expected: Security persistence > syntax persistence

---

## Phase 3: Visualization & Reporting (Week 5)

### 3.1 Propagation Diagrams
Create flow diagrams showing:
- Each iteration as a column
- Hallucinations as nodes (color-coded by type)
- Arrows showing state transitions (persist → mutate → resolve)
- Example: Shows how one API error morphs into a dependency error

### 3.2 Deliverable Charts
1. **Bar chart**: Persistence rate by hallucination type (sorted highest to lowest)
2. **Bar chart**: Mutation rate by hallucination type
3. **Heatmap**: State transition matrix (which states lead to which?)
4. **Line chart**: Survival curve (% of hallucinations surviving to each iteration)
5. **Summary table**: Key statistics per type

### 3.3 Final Report
- Executive summary: What did you find about RQ1 and RQ2?
- Detailed results: Persistence rates with confidence intervals
- Hypothesis validation: Did H1 and H2 hold?
- Implications: What do these patterns tell us about AI-assisted coding?

---

## Datasets to Use

| Dataset | Purpose | Why |
|---------|---------|-----|
| **BigCodeBench** | Library/API-heavy tasks | Best for API hallucinations |
| **DS-1000** | Data science code | Common dependency issues |
| **EvalPlus** (HumanEval+/MBPP+) | Strong test suites | Catch "masked" fixes |
| **SecurityEval** | Security scenarios | Document security persistence |

## Tools & Verification

**Static Analysis (per iteration):**
- Bandit (Python security)
- Semgrep (code patterns)
- CodeQL (vulnerability detection)

**Package Verification:**
- Check PyPI/npm registries for fake packages
- Use `pip show` / `npm info` to verify versions

**Test Execution:**
- Run benchmark unit tests after each iteration
- Record pass/fail counts and error messages

---

## Outputs Expected

```
student_a/outputs/
├── persistence_rates.csv          # Rates by type + overall
├── mutation_rates.csv             # Rates by type + overall
├── state_transitions.csv          # Transition matrix
├── propagation_diagrams/          # PNG files (one per task)
│   ├── task_bigcodebench_001.png
│   ├── task_ds1000_042.png
│   └── ...
├── survival_curves.png            # Line chart: survival by iteration
├── statistical_results.json       # H1/H2 test results + p-values
└── research_report.pdf            # Final paper/presentation
```

---

## Timeline
- **Week 1**: Data setup + manual annotation (coordinate with team)
- **Week 2**: Complete annotations, validate data quality
- **Week 3**: Implement tracking, compute rates
- **Week 4**: Statistical tests, refine analysis
- **Week 5**: Visualizations, final report

## Success Criteria
✓ Processed ≥50 tasks with ≥5 iterations each  
✓ Persistence and mutation rates computed with confidence intervals  
✓ H1 and H2 tested with p-values reported  
✓ Propagation diagrams generated for ≥10 representative tasks  
✓ Clear answer to RQ1 and RQ2 in final report
