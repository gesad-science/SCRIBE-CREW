
from crewai import Agent, Task, LLM
from crewai.tools import tool
from src.entities.config import SystemConfig
import json
import re

from src.entities.config import SystemConfig

config = SystemConfig()


# === TOOLS ===

@tool
def check_metadata_completeness(metadata_json: str) -> str:
    """
    Check if paper metadata has all required fields.
    
    Args:
        metadata_json: JSON string with paper metadata
        
    Returns:
        JSON with validation results
    """
    print(f"[TOOL] Checking metadata completeness...")
    
    try:
        metadata = json.loads(metadata_json)
        
        required_fields = ["title", "authors", "year"]
        optional_fields = ["url", "doi", "arxiv", "bibtex"]
        
        issues = []
        warnings = []
        
        # Check required fields
        for field in required_fields:
            if field not in metadata or not metadata[field]:
                issues.append(f"Missing required field: {field}")
        
        # Check optional fields
        for field in optional_fields:
            if field not in metadata or not metadata[field]:
                warnings.append(f"Missing optional field: {field}")
        
        # Validate year format
        if "year" in metadata:
            year = metadata["year"]
            if not isinstance(year, int) or year < 1900 or year > 2030:
                issues.append(f"Invalid year: {year}")
        
        # Validate authors is a list
        if "authors" in metadata:
            if not isinstance(metadata["authors"], list):
                issues.append("Authors must be a list")
            elif len(metadata["authors"]) == 0:
                issues.append("Authors list is empty")
        
        result = {
            "is_complete": len(issues) == 0,
            "issues": issues,
            "warnings": warnings,
            "has_bibtex": bool(metadata.get("bibtex"))
        }
        
        return json.dumps(result, indent=2)
    
    except Exception as e:
        return json.dumps({"error": f"Failed to validate metadata: {e}"})

@tool
def check_bibtex_validity(bibtex_str: str) -> str:
    """
    Validate BibTeX entry format and structure.
    
    Args:
        bibtex_str: BibTeX entry string
        
    Returns:
        JSON with validation results
    """
    print(f"[TOOL] Validating BibTeX entry...")
    
    issues = []
    warnings = []
    
    if not bibtex_str:
        return json.dumps({
            "is_valid": False,
            "issues": ["BibTeX entry is empty"],
            "warnings": []
        })
    
    # Check if starts with @
    if not bibtex_str.strip().startswith("@"):
        issues.append("BibTeX must start with @ symbol")
    
    # Check balanced braces
    open_count = bibtex_str.count("{")
    close_count = bibtex_str.count("}")
    if open_count != close_count:
        issues.append(f"Unbalanced braces: {open_count} open, {close_count} close")
    
    # Check for citation key
    cite_key_match = re.search(r'@\w+\{([\w\d_:-]+),', bibtex_str)
    if not cite_key_match:
        issues.append("Missing or invalid citation key")
    else:
        citation_key = cite_key_match.group(1)
    
    # Check for required fields
    required_fields = ["title", "author", "year"]
    for field in required_fields:
        pattern = rf'\b{field}\s*=\s*\{{'
        if not re.search(pattern, bibtex_str, re.IGNORECASE):
            warnings.append(f"Missing recommended field: {field}")
    
    result = {
        "is_valid": len(issues) == 0,
        "issues": issues,
        "warnings": warnings,
        "citation_key": cite_key_match.group(1) if cite_key_match else None
    }
    
    return json.dumps(result, indent=2)

@tool
def cross_check_metadata_bibtex(data_json: str) -> str:
    """
    Cross-check consistency between metadata and BibTeX entry.
    
    Args:
        data_json: JSON with both metadata and bibtex fields
        
    Returns:
        JSON with consistency check results
    """
    print(f"[TOOL] Cross-checking metadata and BibTeX...")
    
    try:
        data = json.loads(data_json)
        metadata = data.get("metadata", {})
        bibtex = data.get("bibtex", "")
        
        issues = []
        
        if not bibtex:
            return json.dumps({
                "consistent": True,
                "issues": [],
                "message": "No BibTeX to compare"
            })
        
        # Check title consistency
        meta_title = metadata.get("title", "").lower()
        if meta_title and meta_title not in bibtex.lower():
            issues.append("Title in metadata doesn't match BibTeX")
        
        # Check year consistency
        meta_year = str(metadata.get("year", ""))
        if meta_year and meta_year not in bibtex:
            issues.append("Year in metadata doesn't match BibTeX")
        
        # Check authors consistency (at least one author should match)
        meta_authors = metadata.get("authors", [])
        if meta_authors:
            author_found = False
            for author in meta_authors:
                last_name = author.split()[-1].lower()
                if last_name in bibtex.lower():
                    author_found = True
                    break
            if not author_found:
                issues.append("No authors from metadata found in BibTeX")
        
        result = {
            "consistent": len(issues) == 0,
            "issues": issues,
            "checked_fields": ["title", "year", "authors"]
        }
        
        return json.dumps(result, indent=2)
    
    except Exception as e:
        return json.dumps({"error": f"Failed to cross-check: {e}"})

# === AGENT ===

reference_validator_agent = Agent(
    role="Academic Reference Validator",
    goal="Validate and ensure quality of reference metadata and BibTeX entries",
    backstory="""
You are a meticulous academic quality controller. You check that reference 
metadata is complete, BibTeX entries are valid, and that data is consistent.

You identify missing fields, format errors, and inconsistencies. You provide
clear, actionable validation reports that help improve data quality.
""",
    tools=[
        check_metadata_completeness,
        check_bibtex_validity,
        cross_check_metadata_bibtex
    ],
    llm=config.llm,
    max_iter=5,
    verbose=True,
    allow_delegation=False
)

# === TASK BUILDER ===

def create_validation_task(reference_data: dict) -> Task:
    """
    Create a task for validating reference data.
    
    Args:
        reference_data: Dict with metadata and bibtex
        
    Returns:
        CrewAI Task object
    """
    return Task(
        description=f"""
You received reference data that needs validation:

REFERENCE DATA:
{json.dumps(reference_data, indent=2)}

Your job is to thoroughly validate this data.

VALIDATION STEPS:
1. Use 'check_metadata_completeness' to validate metadata fields
2. If BibTeX is present, use 'check_bibtex_validity' to validate format
3. Use 'cross_check_metadata_bibtex' to ensure consistency

ANALYZE THE RESULTS AND PROVIDE:
- Overall validation status (valid/invalid/warning)
- List of critical issues (must be fixed)
- List of warnings (should be improved)
- Recommendations for improvement

OUTPUT FORMAT (JSON):
{{
  "validation_status": "valid" or "invalid" or "warning",
  "metadata_complete": true/false,
  "bibtex_valid": true/false,
  "data_consistent": true/false,
  "critical_issues": ["issue1", "issue2"],
  "warnings": ["warning1", "warning2"],
  "recommendations": ["rec1", "rec2"]
}}
""",
        agent=reference_validator_agent,
        expected_output="A comprehensive JSON validation report"
    )