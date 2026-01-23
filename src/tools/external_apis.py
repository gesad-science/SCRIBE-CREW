# src/tools/external_apis.py

import time

"""
External API tools - deterministic functions that call external services.
These do NOT use LLMs, only HTTP APIs.
"""

import requests
import re
from typing import Dict, List, Optional
from src.utils import extract_doi, extract_arxiv_id


def search_semantic_scholar(query: str, limit: int = 3, max_retries: int = 5):
    url = (
        "https://api.semanticscholar.org/graph/v1/paper/search"
        f"?query={query}&limit={limit}"
        "&fields=title,authors,year,url,externalIds,citationStyles"
    )

    headers = {
        "User-Agent": "AcademicMultiAgent/1.0",
        # "x-api-key": SEMANTIC_SCHOLAR_API_KEY
    }

    for attempt in range(max_retries):
        try:
            response = requests.get(url, headers=headers)

            if response.status_code == 429:
                wait = 2 ** attempt
                time.sleep(wait)
                continue

            response.raise_for_status()
            data = response.json().get("data", [])

            return {"status": "success", "papers": data}

        except requests.Timeout:
            return {"status": "timeout", "papers": []}

        except requests.HTTPError as e:
            return {
                "status": "error",
                "message": str(e),
                "papers": []
            }

    return {
        "status": "error",
        "message": "Rate limit exceeded after retries",
        "papers": []
    }

def fetch_bibtex_by_doi(doi: str) -> Optional[str]:
    """
    Fetch BibTeX entry using DOI via doi2bib API.
    
    Args:
        doi: Digital Object Identifier
        
    Returns:
        BibTeX string or None if failed
    """
    try:
        from doi2bib3 import fetch_bibtex
        bibtex = fetch_bibtex(doi)
        return bibtex if bibtex else None
    except Exception as e:
        print(f"Error fetching BibTeX for DOI {doi}: {e}")
        return None

def fetch_bibtex_by_arxiv(arxiv_id: str) -> Optional[str]:
    """
    Fetch BibTeX entry using arXiv ID.
    
    Args:
        arxiv_id: arXiv identifier (e.g., "2020.12345")
        
    Returns:
        BibTeX string or None if failed
    """
    try:
        from doi2bib3 import fetch_bibtex
        bibtex = fetch_bibtex(f"arXiv:{arxiv_id}")
        return bibtex if bibtex else None
    except Exception as e:
        print(f"Error fetching BibTeX for arXiv {arxiv_id}: {e}")
        return None

def search_arxiv(query: str, max_results: int = 3) -> List[Dict]:
    """
    Search papers on arXiv.
    
    Args:
        query: Search query
        max_results: Maximum number of results
        
    Returns:
        List of paper dicts
    """
    url = f"http://export.arxiv.org/api/query?search_query=all:{query}&start=0&max_results={max_results}"
    
    try:
        response = requests.get(url, timeout=15)
        if response.status_code != 200:
            return []
        
        # Simple XML parsing
        entries = response.text.split("<entry>")
        papers = []
        
        for entry in entries[1:]:  # Skip header
            # Extract title
            title_match = re.search(r"<title>(.+?)</title>", entry, re.DOTALL)
            title = title_match.group(1).strip() if title_match else ""
            
            # Extract link
            id_match = re.search(r"<id>(.+?)</id>", entry)
            url = id_match.group(1).strip() if id_match else ""
            
            # Extract authors
            authors = re.findall(r"<name>(.+?)</name>", entry)
            
            if title and url:
                papers.append({
                    "title": title,
                    "url": url,
                    "authors": authors
                })
        
        return papers
    
    except Exception as e:
        print(f"Error searching arXiv: {e}")
        return []

def construct_bibtex_manually(paper_info: Dict) -> str:
    """
    Manually construct BibTeX entry from paper metadata.
    Used as fallback when APIs don't provide BibTeX.
    
    Args:
        paper_info: Dict with title, authors, year, etc.
        
    Returns:
        BibTeX string
    """
    title = paper_info.get("title", "Unknown Title")
    authors = paper_info.get("authors", [])
    year = paper_info.get("year", "n.d.")
    url = paper_info.get("url", "")
    
    # Generate citation key
    if authors:
        first_author = authors[0].split()[-1].lower()  # Last name
        first_author = re.sub(r'[^a-z0-9]', '', first_author)
    else:
        first_author = "unknown"
    
    cite_key = f"{first_author}{year}"
    
    # Format authors
    author_str = " and ".join(authors) if authors else "Unknown Author"
    
    # Build BibTeX
    bibtex_parts = [
        f"@article{{{cite_key},",
        f"  title={{{title}}},"
    ]
    
    if authors:
        bibtex_parts.append(f"  author={{{author_str}}},")
    
    bibtex_parts.append(f"  year={{{year}}},")
    
    if url:
        bibtex_parts.append(f"  url={{{url}}},")
    
    bibtex_parts.append("  note={Generated by Academic Multi-Agent System}")
    bibtex_parts.append("}")
    
    return "\n".join(bibtex_parts)

def validate_bibtex_format(bibtex_str: str) -> bool:
    """
    Validate if string is valid BibTeX format.
    
    Args:
        bibtex_str: String to validate
        
    Returns:
        True if valid BibTeX, False otherwise
    """
    if not bibtex_str or not isinstance(bibtex_str, str):
        return False
    
    # Must start with @
    if not bibtex_str.strip().startswith("@"):
        return False
    
    # Must have balanced braces
    if bibtex_str.count("{") != bibtex_str.count("}"):
        return False
    
    # Must have citation key
    if not re.search(r'@\w+\{[\w\d]+,', bibtex_str):
        return False
    
    return True