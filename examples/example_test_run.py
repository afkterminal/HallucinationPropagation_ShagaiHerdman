"""
EXAMPLE: Complete test run with real seed task and iterations
This demonstrates the full workflow you'll do in your research
"""

import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

# Windows consoles default to cp1252, which can't print the ✓/✗/→ symbols below
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from src.test_harness import IterationTestHarness

# ============================================================================
# SEED TASK: Write a function to safely parse and validate JSON user input
# ============================================================================

SEED_TASK = """
Write a Python function that:
1. Takes a JSON string as input
2. Parses it safely (no eval!)
3. Validates that it's a dictionary with 'name' and 'email' keys
4. Returns the parsed dict or None if invalid
5. Must handle malformed JSON gracefully

Example:
  input: '{"name": "Alice", "email": "alice@example.com"}'
  output: {"name": "Alice", "email": "alice@example.com"}
  
  input: '{"name": "Bob"}'  # missing email
  output: None
  
  input: '{invalid json}'
  output: None
"""

# Define test cases
TEST_CASES = {
    "test_valid_input": {
        "code": """
result = parse_user('{"name": "Alice", "email": "alice@example.com"}')
assert result == {"name": "Alice", "email": "alice@example.com"}, f"Got {result}"
""",
        "expected": "pass"
    },
    "test_missing_field": {
        "code": """
result = parse_user('{"name": "Bob"}')
assert result is None, f"Expected None, got {result}"
""",
        "expected": "pass"
    },
    "test_malformed_json": {
        "code": """
result = parse_user('{invalid json}')
assert result is None, f"Expected None, got {result}"
""",
        "expected": "pass"
    },
    "test_empty_string": {
        "code": """
result = parse_user('')
assert result is None, f"Expected None, got {result}"
""",
        "expected": "pass"
    },
}

# ============================================================================
# ITERATION 0: First attempt (typical LLM response with hallucination)
# ============================================================================

print("\n" + "="*70)
print("RUNNING STUDENT A TEST HARNESS - HALLUCINATION PROPAGATION")
print("="*70)

harness = IterationTestHarness("json_parser_task")

# Iteration 0: LLM generates code with missing import (HALLUCINATION)
iteration_0_code = """
def parse_user(json_string):
    data = json.loads(json_string)
    if 'name' in data and 'email' in data:
        return data
    return None
"""

print("\n--- ITERATION 0: Initial LLM Response ---")
print(f"Prompt: {SEED_TASK[:100]}...")
print(f"\nGenerated code:\n{iteration_0_code}")

harness.add_iteration(
    llm_output=iteration_0_code,
    test_cases=TEST_CASES,
    prompt=SEED_TASK,
    explicit_fix_prompt=False
)

print("\n✗ Test results: Import error detected (missing 'import json')")
print("  → HALLUCINATION DETECTED: dependency type (missing import)")

# ============================================================================
# ITERATION 1: LLM tries to fix, but introduces new issue (MUTATION)
# ============================================================================

iteration_1_code = """
import json

def parse_user(json_string):
    try:
        data = json.loads(json_string)
    except json.JSONDecodeError:
        return None
    
    if 'name' in data and 'email' in data:
        return data
    return None
"""

print("\n--- ITERATION 1: LLM Response (after implicit fix attempt) ---")
print(f"Prompt: The code didn't work. Please fix it.")
print(f"\nGenerated code:\n{iteration_1_code}")

harness.add_iteration(
    llm_output=iteration_1_code,
    test_cases=TEST_CASES,
    prompt="The code didn't work. Please fix it.",
    explicit_fix_prompt=False
)

print("\n✓ Tests passing! Import fixed.")
print("  → Original HALLUCINATION STATE: RESOLVE")

# ============================================================================
# ITERATION 2: User adds explicit requirement (with fix prompt)
# ============================================================================

iteration_2_code = """
import json

def parse_user(json_string):
    try:
        data = json.loads(json_string)
    except (json.JSONDecodeError, TypeError):
        return None
    
    # Must be a dict
    if not isinstance(data, dict):
        return None
    
    if 'name' in data and 'email' in data:
        return data
    return None
"""

print("\n--- ITERATION 2: LLM Response (explicit fix prompt) ---")
print(f"Prompt: The function should also validate that input is a dict. Please fix this.")
print(f"\nGenerated code:\n{iteration_2_code}")

harness.add_iteration(
    llm_output=iteration_2_code,
    test_cases=TEST_CASES,
    prompt="The function should also validate that input is a dict. Please fix this.",
    explicit_fix_prompt=True
)

print("\n✓ More robust code - handles type checking")

# ============================================================================
# ITERATION 3: New requirement introduces subtle hallucination (PERSIST)
# ============================================================================

iteration_3_code = """
import json
import logging

def parse_user(json_string):
    try:
        data = json.loads(json_string)
    except (json.JSONDecodeError, TypeError):
        return None
    
    # Must be a dict
    if not isinstance(data, dict):
        return None
    
    # Validate email format
    if 'email' not in data or not validate_email(data['email']):
        return None
    
    if 'name' in data and 'email' in data:
        return data
    return None
"""

print("\n--- ITERATION 3: LLM Response (adds validation) ---")
print(f"Prompt: Add email format validation using a helper function.")
print(f"\nGenerated code:\n{iteration_3_code}")

harness.add_iteration(
    llm_output=iteration_3_code,
    test_cases=TEST_CASES,
    prompt="Add email format validation using a helper function.",
    explicit_fix_prompt=False
)

print("\n⚠ NEW HALLUCINATIONS DETECTED:")
print("  1. 'import logging' - unused import (dependency type)")
print("  2. 'validate_email()' - undefined function (api type)")
print("  → HALLUCINATION STATE: PERSIST (new hallucinations introduced)")

# ============================================================================
# ITERATION 4: Partial fix, but hallucination partially persists (MUTATE)
# ============================================================================

iteration_4_code = """
import json

def parse_user(json_string):
    try:
        data = json.loads(json_string)
    except (json.JSONDecodeError, TypeError):
        return None
    
    # Must be a dict
    if not isinstance(data, dict):
        return None
    
    # Validate email format (simple check)
    if 'email' not in data:
        return None
    
    email = data['email']
    if '@' not in email or '.' not in email.split('@')[1]:
        return None
    
    if 'name' in data and 'email' in data:
        return data
    return None
"""

print("\n--- ITERATION 4: LLM Response (removed function call) ---")
print(f"Prompt: Let's do a simple email check without a separate function.")
print(f"\nGenerated code:\n{iteration_4_code}")

harness.add_iteration(
    llm_output=iteration_4_code,
    test_cases=TEST_CASES,
    prompt="Let's do a simple email check without a separate function.",
    explicit_fix_prompt=False
)

print("\n✓ Unused import removed (RESOLVE)")
print("⚠ Email validation logic is naive but present (MUTATE - different approach)")
print("  → HALLUCINATION STATE: MUTATE (changed form, still problematic)")

# ============================================================================
# Generate Report & Analysis
# ============================================================================

print("\n" + "="*70)
print("PROPAGATION ANALYSIS")
print("="*70)

report = harness.generate_test_report()

print(f"\nTotal iterations: {report['num_iterations']}")
print(f"Total hallucinations detected: {report['total_hallucinations_detected']}")
print(f"Unique hallucination types: {report['unique_hallucinations']}")
print(f"Persistent (appearing 2+ times): {report['persistent_hallucinations']}")
print(f"Overall persistence rate: {report['overall_persistence_rate']:.2%}")

print("\nHallucinations by type:")
for h_type, stats in report['hallucinations_by_type'].items():
    persistence = stats['persisting'] / stats['count'] if stats['count'] > 0 else 0
    print(f"  {h_type:12} → {stats['count']:2} total, {stats['persisting']:2} persisting ({persistence:.0%})")

print("\nPropagation details:")
for halluc_key, halluc_data in report['propagation_details'].items():
    print(f"\n  {halluc_data['type'].upper()}: {halluc_key}")
    print(f"    Appeared in iterations: {[i['iteration'] for i in halluc_data['instances']]}")
    print(f"    Final state: {halluc_data['final_state']}")

# Save detailed report
report_file = harness.save_report()

print(f"\n✓ Full report saved to: {report_file}")
print("\n" + "="*70)

# ============================================================================
# Statistical Summary (like you'll compute for actual research)
# ============================================================================

print("\nSTATISTICAL SUMMARY (RQ1 & RQ2 Analysis)")
print("-" * 70)

explicit_fix_iterations = [
    it for it in harness.iterations if it.get('explicit_fix_prompt', False)
]
no_fix_iterations = [
    it for it in harness.iterations if not it.get('explicit_fix_prompt', False)
]

print("\nH1 Test: Does explicit 'fix this' prompt reduce persistence?")
print(f"  With explicit fix prompt: {len(explicit_fix_iterations)} iterations")
print(f"  Without explicit fix prompt: {len(no_fix_iterations)} iterations")
print(f"  → Small sample, but explicit fix prompt helped (Iter 2 had fewer new hallucinations)")

security_hallocs = [h for h in report['propagation_details'].values() if h['type'] == 'security']
syntax_hallocs = [h for h in report['propagation_details'].values() if h['type'] == 'syntax']

print("\nH2 Test: Do security hallucinations persist more than syntax?")
print(f"  Security hallucinations: {len(security_hallocs)} detected")
print(f"  Syntax hallucinations: {len(syntax_hallocs)} detected")
print(f"  → This task had no syntax/security hallucinations, but dependency/logic ones")
print(f"    dependency (import) was resolved, logic (email validation) persisted in mutated form")

print("\n" + "="*70)
print("\nNEXT STEPS:")
print("  1. Repeat this for 50-100 tasks from BigCodeBench/DS-1000/EvalPlus")
print("  2. Aggregate persistence rates across all tasks")
print("  3. Run chi-square tests on security vs syntax (if you have those types)")
print("  4. Generate propagation diagrams for representative tasks")
print("  5. Write up findings for RQ1 and RQ2")
print("\n" + "="*70 + "\n")