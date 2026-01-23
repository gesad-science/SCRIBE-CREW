# src/agents/governance_agent.py
"""
Governance Agent - validates plans and enforces system policies.
This agent ensures that execution plans are well-formed and compliant.
"""

from crewai import Agent, Task
from crewai.tools import tool
from src.entities.config import SystemConfig
config = SystemConfig()
from src.utils import safe_json_parse
import json
import re

# System policies
SYSTEM_POLICIES = [
    "All plans must be valid JSON with 'steps' array",
    "Each step must have: step number, action, and input fields",
    "Actions must be one of: find_reference, generate_bibtex, validate_reference",
    "No personal identifiable information (PII) should be present",
    "Plans should be efficient (minimize redundant steps)"
]

# === TOOLS ===

@tool
def get_system_policies() -> str:
    """
    Get the list of system policies that plans must comply with.
    
    Returns:
        JSON string with system policies
    """
    print(f"[TOOL] Retrieving system policies...")
    
    result = {
        "policies": SYSTEM_POLICIES,
        "policy_count": len(SYSTEM_POLICIES)
    }
    
    return json.dumps(result, indent=2)
@tool
def validate_plan_structure(plan_json: str) -> str:
    """
    Validate the structure of an execution plan.

    Expected schema:

    {
      "plan": [
        {
          "agent": "string",
          "action": "string"
        }
      ]
    }
    """
    print("[TOOL] Validating plan structure...")

    issues = []
    warnings = []

    plan_data = safe_json_parse(plan_json)

    if not plan_data:
        return json.dumps({
            "is_valid": False,
            "issues": ["Plan is not valid JSON"],
            "warnings": []
        })

    # Top-level validation
    if "plan" not in plan_data:
        return json.dumps({
            "is_valid": False,
            "issues": ["Missing top-level key 'plan'"],
            "warnings": []
        })

    plan = plan_data["plan"]

    if not isinstance(plan, list):
        return json.dumps({
            "is_valid": False,
            "issues": ["'plan' must be an array"],
            "warnings": []
        })

    if len(plan) == 0:
        return json.dumps({
            "is_valid": False,
            "issues": ["'plan' array is empty"],
            "warnings": []
        })

    # Validate each plan item
    for i, step in enumerate(plan):
        step_index = i + 1

        if not isinstance(step, dict):
            issues.append(f"Plan item {step_index} must be an object")
            continue

        if "agent" not in step:
            issues.append(f"Plan item {step_index} missing 'agent' field")

        if "action" not in step:
            issues.append(f"Plan item {step_index} missing 'action' field")

        # Optional sanity warnings
        if "agent" in step and not isinstance(step["agent"], str):
            issues.append(f"Plan item {step_index} 'agent' must be a string")

        if "action" in step and not isinstance(step["action"], str):
            issues.append(f"Plan item {step_index} 'action' must be a string")

    return json.dumps({
        "is_valid": len(issues) == 0,
        "issues": issues,
        "warnings": warnings,
        "step_count": len(plan)
    }, indent=2)

@tool
def detect_pii(text: str) -> str:
    """
    Detect potential Personal Identifiable Information (PII) in text.
    
    Args:
        text: Text to scan for PII
        
    Returns:
        JSON with PII detection results
    """
    print(f"[TOOL] Scanning for PII...")
    
    pii_patterns = {
        "email": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        "phone": r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
        "ssn": r'\b\d{3}-\d{2}-\d{4}\b',
        "credit_card": r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b'
    }
    
    detected = []
    
    for pii_type, pattern in pii_patterns.items():
        matches = re.findall(pattern, text)
        if matches:
            detected.append({
                "type": pii_type,
                "count": len(matches),
                "examples": matches[:2]  # Show first 2 examples
            })
    
    result = {
        "pii_found": len(detected) > 0,
        "detected_types": detected,
        "severity": "high" if detected else "none"
    }
    
    return json.dumps(result, indent=2)

@tool
def check_plan_efficiency(plan_json: str) -> str:
    """
    Check if an execution plan is efficient (no redundant steps).
    
    Args:
        plan_json: JSON string with the execution plan
        
    Returns:
        JSON with efficiency analysis
    """
    print(f"[TOOL] Analyzing plan efficiency...")
    
    plan = safe_json_parse(plan_json)
    
    if not plan or "steps" not in plan:
        return json.dumps({
            "is_efficient": False,
            "issues": ["Cannot analyze invalid plan"]
        })
    
    steps = plan["steps"]
    issues = []
    suggestions = []
    
    # Check for duplicate actions with same input
    seen_actions = {}
    for i, step in enumerate(steps):
        action = step.get("action", "")
        input_text = step.get("input", "")
        key = f"{action}:{input_text}"
        
        if key in seen_actions:
            issues.append(
                f"Step {i+1} duplicates step {seen_actions[key]}: "
                f"same action and input"
            )
        else:
            seen_actions[key] = i + 1
    
    # Check for excessive steps
    if len(steps) > 5:
        suggestions.append(
            f"Plan has {len(steps)} steps. Consider consolidating if possible."
        )
    
    # Check if validation comes before generation
    actions = [s.get("action") for s in steps]
    if "validate_reference" in actions and "generate_bibtex" in actions:
        val_idx = actions.index("validate_reference")
        gen_idx = actions.index("generate_bibtex")
        if val_idx < gen_idx:
            suggestions.append(
                "Consider validating after generating BibTeX, not before"
            )
    
    result = {
        "is_efficient": len(issues) == 0,
        "issues": issues,
        "suggestions": suggestions,
        "step_count": len(steps)
    }
    
    return json.dumps(result, indent=2)

# === AGENT ===

governance_agent = Agent(
    role="System Governance Controller",
    goal="Ensure all plans comply with policies and are well-structured",
    backstory="""
You are the system's policy enforcement officer. You validate that all 
execution plans follow the rules, are properly structured, contain no 
sensitive information, and are efficient.

You provide clear, constructive feedback when plans need improvement.
You help maintain system integrity and data quality.
""",
    tools=[
        get_system_policies,
        validate_plan_structure,
        detect_pii,
        check_plan_efficiency
    ],
    llm=config.llm,
    max_iter=config.max_agent_iterations,
    verbose=True,
    allow_delegation=False
)

# === TASK BUILDER ===

def create_governance_task(plan_or_data: str) -> Task:
    """
    Create a task for validating a plan or execution data.
    
    Args:
        plan_or_data: Plan JSON or execution data to validate
        
    Returns:
        CrewAI Task object
    """
    return Task(
        description=f"""
You received content that needs governance validation:

CONTENT:
{plan_or_data}

Your job is to thoroughly validate this content against system policies.

VALIDATION STEPS:
1. Use 'get_system_policies' to retrieve current policies
2. Use 'validate_plan_structure' to check structure
3. Use 'detect_pii' to scan for sensitive information
4. Use 'check_plan_efficiency' to analyze efficiency

PROVIDE A COMPREHENSIVE REPORT:
- Whether the content is approved or rejected
- List of policy violations (if any)
- List of structural issues (if any)
- PII detection results
- Efficiency recommendations

OUTPUT FORMAT (JSON):
{{
  "approved": true/false,
  "status": "approved" or "rejected" or "needs_revision",
  "policy_violations": ["violation1", "violation2"],
  "structural_issues": ["issue1", "issue2"],
  "pii_detected": true/false,
  "efficiency_score": "high" or "medium" or "low",
  "recommendations": ["rec1", "rec2"],
  "summary": "brief summary of validation"
}}
""",
        agent=governance_agent,
        expected_output="A comprehensive governance validation report in JSON format"
    )