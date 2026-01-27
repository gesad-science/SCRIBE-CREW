from crewai import Agent, Task, LLM
from crewai.tools import tool
from src.entities.config import SystemConfig
from src.tools.external_apis import search_semantic_scholar
from src.utils import guess_title_from_reference, extract_doi, extract_arxiv_id
import json
from src.utils import normalize_json

from src.entities.config import SystemConfig
config = SystemConfig()

# === TOOLS ===

@tool
def search_paper_by_title(title: str) -> str:
    """
    Search for an academic paper using its title.
    This tool queries Semantic Scholar API.
    
    Args:
        title: The paper title to search for
        
    Returns:
        JSON string with search results containing title, authors, year, url, and bibtex
    """
    print(f"[TOOL] Searching for paper: {title[:80]}...")

    title = normalize_json(title)

    print(f"Normalized title: {title}")
    
    result = search_semantic_scholar(title, limit=1)
    
    return json.dumps(result, indent=2, ensure_ascii=False)

@tool
def extract_identifiers_from_reference(reference_text: str) -> str:
    """
    Extract DOI and arXiv ID from a reference string.
    
    Args:
        reference_text: The full reference text
        
    Returns:
        JSON string with extracted identifiers
    """
    print(f"[TOOL] Extracting identifiers from reference... {reference_text}")

    reference_text = normalize_json(reference_text)

    print(f"New reference text: {reference_text}")
    
    doi = extract_doi(reference_text)
    arxiv = extract_arxiv_id(reference_text)
    
    result = {
        "doi": doi,
        "arxiv": arxiv,
        "has_doi": doi is not None,
        "has_arxiv": arxiv is not None
    }
    
    return json.dumps(result, indent=2)

@tool
def guess_title_tool(reference_text: str) -> str:
    """
    Estimate the paper title from a reference string.
    Usually the title is the longest sentence in the reference.
    
    Args:
        reference_text: The full reference text
        
    Returns:
        The estimated title
    """
    print(f"[TOOL] Guessing title from reference...")
    
    title = guess_title_from_reference(reference_text)
    
    return title

# === AGENT ===

reference_finder_agent = Agent(
    role="Academic Reference Finder",
    goal="Find and retrieve metadata JSON for academic papers from reference strings",
    backstory="""
You are an expert academic librarian specialized in finding papers from 
incomplete or formatted references. You use search tools to locate papers
and extract their metadata including title, authors, year, and BibTeX.

You NEVER invent or hallucinate data. You ONLY use information returned 
by your tools. If a paper cannot be found, you report that clearly. And you only can return JSON in the specified format.
""",
    tools=[search_paper_by_title, extract_identifiers_from_reference, guess_title_tool],
    llm=config.llm,
    max_iter=3,
    verbose=True,
    allow_delegation=False
)

# === TASK BUILDER ===

def create_reference_task(reference_text: str) -> Task:
    """
    Create a task for finding a single reference.
    
    Args:
        reference_text: The reference string to process
        
    Returns:
        CrewAI Task object
    """
    return Task(
        description=f"""
You received the following academic reference:

REFERENCE:
\"\"\"
{reference_text}
\"\"\"

Your job is to find this paper and extract its metadata.

STEPS:
1. Use 'extract_identifiers_from_reference' to check for DOI or arXiv ID
2. Use 'guess_title_tool' to estimate the paper title
3. Use 'search_paper_by_title' to search for the paper
4. Analyze the search results and select the most relevant paper
5. Return the paper metadata in the specified JSON format
6. If you already have the paper information, return it in the specified format.

IMPORTANT RULES:
- Use each tool only ONCE
- Do NOT invent authors, titles, or any data
- ONLY use information returned by the tools
- If the paper is not found, set "status": "not_found"
- Select the FIRST result from search as the most relevant

OUTPUT FORMAT (JSON):
{{
  "original_reference": "the reference text you received",
  "status": "found" or "not_found",
  "paper": {{
    "title": "paper title from search results",
    "authors": ["author1", "author2"],
    "year": 2020,
    "url": "https://...",
    "doi": "10.xxxx/yyyy or null",
    "arxiv": "arxiv_id or null",
    "bibtex": "bibtex string from search or null"
  }}
}}
""",
        agent=reference_finder_agent,
        expected_output="A JSON object with the reference metadata or not_found status"
    )