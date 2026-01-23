# src/agents/bibtex_agent.py
"""
BibTeX Generator Agent - creates or improves BibTeX entries.
This agent takes paper metadata and produces valid BibTeX entries.
"""

from crewai import Agent, Task
from crewai.tools import tool
from src.tools.external_apis import (
    fetch_bibtex_by_doi, 
    fetch_bibtex_by_arxiv,
    construct_bibtex_manually,
    validate_bibtex_format
)
import json
from src.entities.config import SystemConfig
config = SystemConfig()

# === TOOLS ===

@tool
def fetch_bibtex_from_doi(doi: str) -> str:
    """
    Fetch BibTeX entry using a DOI (Digital Object Identifier).
    
    Args:
        doi: The DOI string (e.g., "10.1234/example.2020")
        
    Returns:
        BibTeX string or error message
    """
    print(f"[TOOL] Fetching BibTeX for DOI: {doi}")
    
    bibtex = fetch_bibtex_by_doi(doi)
    
    if bibtex:
        return bibtex
    else:
        return json.dumps({"error": "Could not fetch BibTeX for this DOI"})

@tool
def fetch_bibtex_from_arxiv(arxiv_id: str) -> str:
    """
    Fetch BibTeX entry using an arXiv ID.
    
    Args:
        arxiv_id: The arXiv identifier (e.g., "2020.12345")
        
    Returns:
        BibTeX string or error message
    """
    print(f"[TOOL] Fetching BibTeX for arXiv: {arxiv_id}")
    
    bibtex = fetch_bibtex_by_arxiv(arxiv_id)
    
    if bibtex:
        return bibtex
    else:
        return json.dumps({"error": "Could not fetch BibTeX for this arXiv ID"})

@tool
def create_bibtex_manually(paper_json: str) -> str:
    """
    Manually construct a BibTeX entry from paper metadata.
    Use this when DOI/arXiv fetching fails or when no BibTeX is available.
    
    Args:
        paper_json: JSON string with paper metadata (title, authors, year, url)
        
    Returns:
        Constructed BibTeX string
    """
    print(f"[TOOL] Manually constructing BibTeX entry...")
    
    try:
        paper_info = json.loads(paper_json)
        bibtex = construct_bibtex_manually(paper_info)
        return bibtex
    except Exception as e:
        return json.dumps({"error": f"Failed to construct BibTeX: {e}"})

@tool
def validate_bibtex(bibtex_str: str) -> str:
    """
    Validate if a string is a valid BibTeX entry.
    
    Args:
        bibtex_str: The BibTeX string to validate
        
    Returns:
        JSON with validation result
    """
    print(f"[TOOL] Validating BibTeX format...")
    
    is_valid = validate_bibtex_format(bibtex_str)
    
    result = {
        "is_valid": is_valid,
        "message": "Valid BibTeX format" if is_valid else "Invalid BibTeX format"
    }
    
    return json.dumps(result, indent=2)

# === AGENT ===

bibtex_generator_agent = Agent(
    role="BibTeX Entry Generator",
    goal="Generate or retrieve valid BibTeX entries for academic papers",
    backstory="""
You are a bibliographic expert specialized in creating and managing BibTeX 
entries. You know how to fetch BibTeX from various sources (DOI, arXiv) and 
can manually construct valid entries when needed.

You ALWAYS ensure BibTeX entries follow proper formatting with:
- Valid entry type (@article, @inproceedings, etc.)
- Proper citation key
- Required fields (title, author, year)
- Balanced braces
""",
    tools=[
        fetch_bibtex_from_doi,
        fetch_bibtex_from_arxiv,
        create_bibtex_manually,
        validate_bibtex
    ],
    llm=config.llm,
    max_iter=config.max_agent_iterations,
    verbose=True,
    allow_delegation=False
)

# === TASK BUILDER ===

def create_bibtex_task(paper_metadata: dict) -> Task:
    """
    Create a task for generating BibTeX from paper metadata.
    
    Args:
        paper_metadata: Dict with paper information
        
    Returns:
        CrewAI Task object
    """
    return Task(
        description=f"""
You received metadata for an academic paper:

PAPER METADATA:
{json.dumps(paper_metadata, indent=2)}

Your job is to obtain or create a valid BibTeX entry for this paper.

STEPS:
1. Check if the metadata already contains a valid BibTeX entry
   - If yes, validate it using 'validate_bibtex' tool
   - If valid, return it
   
2. If no BibTeX or invalid:
   - If DOI is available, use 'fetch_bibtex_from_doi'
   - If arXiv ID is available, use 'fetch_bibtex_from_arxiv'
   - If both fail or unavailable, use 'create_bibtex_manually'

3. Validate the final BibTeX entry

4. Return the result in JSON format

IMPORTANT RULES:
- Try DOI/arXiv fetching FIRST (they provide authoritative BibTeX)
- Only use manual construction as LAST RESORT
- ALWAYS validate the final BibTeX before returning
- Do NOT modify or "improve" fetched BibTeX entries
- Use tools efficiently (don't retry failed operations)

OUTPUT FORMAT (JSON):
{{
  "bibtex": "the valid BibTeX entry",
  "source": "doi" or "arxiv" or "manual" or "provided",
  "is_valid": true,
  "citation_key": "extracted citation key"
}}
""",
        agent=bibtex_generator_agent,
        expected_output="A JSON object containing a valid BibTeX entry"
    )