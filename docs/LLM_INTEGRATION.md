# LLM Integration

How to generate real multi-turn coding trajectories with an LLM and log them
through `IterationTestHarness`, so they can be analyzed like the example in
[QUICK_START.md](QUICK_START.md).

The harness itself is model-agnostic: it only needs the code the model
produced at each iteration. This guide uses Claude through the official
Anthropic Python SDK. For the shared corpus the team plans to use InterCode or
MINT as the multi-turn harness; the script below is a lightweight stand-in for
pilot runs and for checking that the analysis pipeline works end to end.

## 1. Setup

```bash
python -m pip install anthropic
```

Create an API key in the [Claude Console](https://console.anthropic.com/) and
set it as an environment variable. Never commit the key to the repository.

```powershell
# Windows PowerShell (current session only)
$env:ANTHROPIC_API_KEY = "sk-ant-..."
```

```bash
# macOS / Linux
export ANTHROPIC_API_KEY="sk-ant-..."
```

## 2. How a session works

Each task is one conversation that runs for `NUM_ITERATIONS` turns:

1. **Iteration 0** — the seed prompt from the benchmark task.
2. The reply's code is extracted and passed to `harness.add_iteration()`,
   which runs the unit tests and detects hallucinations.
3. **Iterations 1+** — a standardized follow-up prompt. Which prompt is sent
   depends on the task's experimental condition (this is what H1 compares):

   | Condition | Follow-up when problems were detected | `explicit_fix_prompt` |
   |---|---|---|
   | explicit fix | `FIX_PROMPT` listing the detected problems | `True` |
   | control | `NEUTRAL_PROMPT` ("Please continue improving the code.") | `False` |

   In the explicit-fix condition the neutral prompt is still used for
   iterations where nothing was detected, and those are logged as `False`.

The conversation history is sent in full every turn (the API is stateless), so
the model sees its earlier attempts, the same way a developer's chat would.

## 3. Script

Save as `generate_trajectories.py` in the repository root.

```python
import re

import anthropic

from src.test_harness import IterationTestHarness

MODEL = "claude-opus-5"
NUM_ITERATIONS = 5  # the shared corpus needs >= 5 refinement iterations per task

SYSTEM_PROMPT = (
    "You are a Python coding assistant. Always reply with the complete, "
    "updated program in a single ```python code block."
)

# Standardized follow-up prompts. Keep the wording fixed across all tasks so
# the only thing that differs between conditions is the explicit fix request.
FIX_PROMPT = "The code has a problem:\n{problems}\nPlease fix this."
NEUTRAL_PROMPT = "Please continue improving the code."

client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from the environment

CODE_BLOCK = re.compile(r"```(?:python|py)?[ \t]*\n(.*?)```", re.DOTALL)


def extract_code(text: str) -> str:
    """Return the last fenced code block, or the whole reply if there is none."""
    blocks = CODE_BLOCK.findall(text)
    return blocks[-1].strip() if blocks else text.strip()


def describe_problems(iteration_data: dict) -> str:
    """Summarize what the harness detected, for use in FIX_PROMPT."""
    lines = [f"- {h['description']}" for h in iteration_data["hallucinations_detected"]]
    return "\n".join(lines) or "- The output does not meet the requirements."


def run_session(task_id: str, seed_prompt: str, test_cases: dict, explicit_fix: bool):
    """
    Run one multi-turn coding session and log every iteration in the harness.

    explicit_fix=True  -> follow-ups name the detected problems and ask for a fix
    explicit_fix=False -> follow-ups use the neutral prompt (control condition)
    """
    harness = IterationTestHarness(task_id)
    messages = []
    prompt, is_fix_prompt = seed_prompt, False

    for _ in range(NUM_ITERATIONS):
        messages.append({"role": "user", "content": prompt})
        response = client.messages.create(
            model=MODEL,
            max_tokens=16000,
            system=SYSTEM_PROMPT,
            messages=messages,
        )
        if response.stop_reason == "refusal":
            raise RuntimeError(f"{task_id}: model refused at iteration {len(harness.iterations)}")

        # Keep the full response (including thinking blocks) in the history
        messages.append({"role": "assistant", "content": response.content})
        reply = "".join(block.text for block in response.content if block.type == "text")

        iteration_data = harness.add_iteration(
            llm_output=extract_code(reply),
            test_cases=test_cases,
            prompt=prompt,
            explicit_fix_prompt=is_fix_prompt,
        )

        if explicit_fix and iteration_data["hallucinations_detected"]:
            prompt = FIX_PROMPT.format(problems=describe_problems(iteration_data))
            is_fix_prompt = True
        else:
            prompt, is_fix_prompt = NEUTRAL_PROMPT, False

    harness.save_report()
    return harness
```

Usage, with test cases in the same format as
[examples/example_test_run.py](../examples/example_test_run.py):

```python
from generate_trajectories import run_session

run_session("bigcodebench_001", seed_prompt, test_cases, explicit_fix=True)
```

Each call writes `test_outputs/test_report_<task_id>.json`, which
`HallucinationTracker.load_harness_report()` reads directly.

## 4. Assigning conditions

Assign each **task** to one condition (explicit fix or control), not each
iteration, so the two groups in the H1 chi-square test are independent.
Randomize with a fixed seed so the assignment is reproducible:

```python
import random

rng = random.Random(42)
conditions = {task_id: rng.random() < 0.5 for task_id in task_ids}
```

## 5. Research notes

- **Record the model.** Store the exact model ID (`MODEL`) and the date of the
  run with the corpus, for example in `CorpusMetadata.llm_model` from
  [src/hallucination_taxonomy.py](../src/hallucination_taxonomy.py). Results
  from different models must not be pooled without saying so.
- **Keep one model per trajectory.** The API's automatic fallback feature
  (which re-runs refused requests on a different model) is deliberately not
  used here: it would mix models inside a single trajectory. A refusal stops
  the session instead; log it and exclude or rerun that task.
- **Refusals are rare but possible** on security-themed prompts
  (SecurityEval/CyberSecEval). Count them and report them as a limitation.
- **Cost.** Every turn resends the whole conversation, so cost grows with the
  number of iterations. Run a handful of tasks first and check usage in the
  Claude Console before launching the full 50–100 task corpus.
- **The harness's security check is a simple pattern scan.** Before reporting
  security results, run Bandit/Semgrep on each iteration's code as the team
  plan requires (see [RESEARCH_CHECKLIST.md](RESEARCH_CHECKLIST.md)).
