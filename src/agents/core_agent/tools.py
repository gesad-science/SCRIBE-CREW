##### HARDCODED BY NOW #####

# === TOOLS FOR CORE AGENT ===

from crewai.tools import tool
from crewai import Crew, Task
import json
from src.entities.config import SystemConfig
config = SystemConfig()

# Import specialized agents
from src.agents.reference_agent import reference_finder_agent, create_reference_task
from src.agents.bibtex_agent import bibtex_generator_agent, create_bibtex_task
from src.agents.validator_agent import reference_validator_agent, create_validation_task
from src.agents.governance_agent import governance_agent, create_governance_task

import json
from pathlib import Path
from datetime import datetime
from typing import Dict

@tool
def save_plan(plan_json:Dict) -> Path:
    """
    Save a plan JSON to a .pln file.

    Args:
        plan_json (dict | str): The plan as a Python dict or JSON string.
    Returns:
        Path: Path to the saved .pln file.
    """

    directory = "plans"

    if isinstance(plan_json, str):
        plan_data = json.loads(plan_json)
    elif isinstance(plan_json, Dict):
        plan_data = plan_json
    else:
        raise TypeError("plan_json must be a dict or a JSON string")

    if "plan" not in plan_data or not isinstance(plan_data["plan"], list):
        raise ValueError("Invalid plan format: missing 'plan' list")

    Path(directory).mkdir(parents=True, exist_ok=True)

    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    file_path = Path(directory) / f"plan_{timestamp}.pln"

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(plan_data, f, indent=2, ensure_ascii=False)

    return file_path



@tool
def delegate_to_reference_finder(reference_text: str) -> str:
    """
    Delegate to the Reference Finder Agent to search for a paper.
    
    Args:
        reference_text: The academic reference string to find
        
    Returns:
        JSON string with paper metadata
    """
    print(f"\n[CORE] Delegating to Reference Finder Agent...")
    print(f"[CORE] Reference: {reference_text[:100]}...\n")
    
    task = create_reference_task(reference_text)
    
    crew = Crew(
        agents=[reference_finder_agent],
        tasks=[task],
        verbose=True,
        max_rpm=config.max_rpm
    )
    
    try:
        result = crew.kickoff()
        return str(result)
    except Exception as e:
        return json.dumps({
            "status": "error",
            "message": f"Reference Finder failed: {e}"
        })

@tool
def delegate_to_bibtex_generator(paper_metadata_json: str) -> str:
    """
    Delegate to the BibTeX Generator Agent to create/fetch BibTeX entry.
    
    Args:
        paper_metadata_json: JSON string with paper metadata
        
    Returns:
        JSON string with BibTeX entry
    """
    print(f"\n[CORE] Delegating to BibTeX Generator Agent...\n")
    
    try:
        paper_metadata = json.loads(paper_metadata_json)
    except:
        return json.dumps({
            "error": "Invalid JSON for paper metadata"
        })
    
    task = create_bibtex_task(paper_metadata)
    
    crew = Crew(
        agents=[bibtex_generator_agent],
        tasks=[task],
        verbose=True,
        max_rpm=config.max_rpm
    )
    
    try:
        result = crew.kickoff()
        return str(result)
    except Exception as e:
        return json.dumps({
            "status": "error",
            "message": f"BibTeX Generator failed: {e}"
        })

@tool
def delegate_to_validator(reference_data_json: str) -> str:
    """
    Delegate to the Reference Validator Agent to validate data quality.
    
    Args:
        reference_data_json: JSON string with reference data to validate
        
    Returns:
        JSON string with validation report
    """
    print(f"\n[CORE] Delegating to Reference Validator Agent...\n")
    
    try:
        reference_data = json.loads(reference_data_json)
    except:
        return json.dumps({
            "error": "Invalid JSON for reference data"
        })
    
    task = create_validation_task(reference_data)
    
    crew = Crew(
        agents=[reference_validator_agent],
        tasks=[task],
        verbose=True,
        max_rpm=config.max_rpm
    )
    
    try:
        result = crew.kickoff()
        return str(result)
    except Exception as e:
        return json.dumps({
            "status": "error",
            "message": f"Validator failed: {e}"
        })

@tool
def delegate_to_governance(plan_json: str) -> str:
    """
    Delegate to the Governance Agent to validate a plan.
    
    Args:
        plan_json: JSON string with execution plan or other information to validate
        
    Returns:
        JSON string with governance validation report
    """
    print(f"\n[CORE] Delegating to Governance Agent...\n")

    plan_json = str(plan_json)
    
    task = create_governance_task(plan_json)
    
    crew = Crew(
        agents=[governance_agent],
        tasks=[task],
        verbose=True,
        max_rpm=config.max_rpm
    )
    
    try:
        result = crew.kickoff()
        return str(result)
    except Exception as e:
        return json.dumps({
            "status": "error",
            "message": f"Governance validation failed: {e}"
        })
