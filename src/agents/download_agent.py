import os
import requests
from crewai import Agent, Task
from crewai.tools import tool
from urllib.parse import urlparse
from src.entities.config import SystemConfig
import json

config = SystemConfig()

PDF_DIR = "pdfs"
os.makedirs(PDF_DIR, exist_ok=True)

@tool
def resolve_doi(doi: str) -> str:
    """
    Resolve a DOI to its landing page URL.

    Args:
        doi: DOI string

    Returns:
        JSON with resolved URL
    """

    doi = doi.strip()

    if doi.startswith("http"):
        url = doi
    else:
        url = f"https://doi.org/{doi}"

    response = requests.get(url, allow_redirects=True)

    result = {
        "doi": doi,
        "resolved_url": response.url
    }

    return json.dumps(result, indent=2)

@tool
def find_pdf_link(url: str) -> str:
    """
    Attempt to locate a PDF from a given URL.

    Args:
        url: page url

    Returns:
        JSON with possible PDF link
    """

    if url.endswith(".pdf"):
        return json.dumps({
            "pdf_url": url
        })

    candidate = url.rstrip("/") + ".pdf"

    return json.dumps({
        "pdf_url": candidate
    })

@tool
def download_pdf(pdf_url: str) -> str:
    """
    Download a PDF file into the .pdfs directory.

    Args:
        pdf_url: direct URL to PDF

    Returns:
        JSON with download status and file path
    """

    try:
        response = requests.get(pdf_url, stream=True, timeout=30)

        if response.status_code != 200:
            return json.dumps({
                "status": "failed",
                "reason": f"status_code_{response.status_code}"
            })

        filename = os.path.basename(urlparse(pdf_url).path)

        if not filename.endswith(".pdf"):
            filename = filename + ".pdf"

        filepath = os.path.join(PDF_DIR, filename)

        with open(filepath, "wb") as f:
            for chunk in response.iter_content(1024):
                f.write(chunk)

        return json.dumps({
            "status": "downloaded",
            "file_path": filepath
        })

    except Exception as e:
        return json.dumps({
            "status": "failed",
            "reason": str(e)
        })

@tool
def query_unpaywall(doi: str) -> str:
    """
    Query Unpaywall to find open access PDF links.

    Args:
        doi: DOI

    Returns:
        JSON with open access locations
    """

    doi = doi.strip().replace("https://doi.org/", "")

    email = "test@example.com"  # Unpaywall exige email
    url = f"https://api.unpaywall.org/v2/{doi}?email={email}"

    try:
        r = requests.get(url, timeout=20)
        data = r.json()

        locations = []

        for loc in data.get("oa_locations", []):
            locations.append({
                "url": loc.get("url"),
                "pdf_url": loc.get("url_for_pdf"),
                "host_type": loc.get("host_type"),
                "version": loc.get("version")
            })

        result = {
            "doi": doi,
            "is_oa": data.get("is_oa"),
            "locations": locations
        }

        return json.dumps(result, indent=2)

    except Exception as e:
        return json.dumps({
            "status": "error",
            "reason": str(e)
        })

from crewai.tools import tool
import requests
import json

@tool
def query_crossref_by_doi(doi: str) -> str:
    """
    Query Crossref API for DOI metadata and possible PDF links.

    Args:
        doi: DOI string

    Returns:
        JSON metadata from Crossref
    """

    doi = doi.strip().replace("https://doi.org/", "")

    url = f"https://api.crossref.org/works/{doi}"

    try:
        r = requests.get(url, timeout=20)
        data = r.json()

        links = []
        if "link" in data["message"]:
            for l in data["message"]["link"]:
                links.append({
                    "url": l.get("URL"),
                    "content_type": l.get("content-type")
                })

        result = {
            "doi": doi,
            "title": data["message"].get("title", [None])[0],
            "publisher": data["message"].get("publisher"),
            "year": data["message"].get("issued", {}).get("date-parts", [[None]])[0][0],
            "links": links
        }

        return json.dumps(result, indent=2)

    except Exception as e:
        return json.dumps({
            "status": "error",
            "reason": str(e)
        })

@tool
def query_arxiv(arxiv_id: str) -> str:
    """
    Get arXiv PDF link from arXiv ID.
    """

    arxiv_id = arxiv_id.replace("arxiv:", "").strip()

    pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"

    return json.dumps({
        "arxiv_id": arxiv_id,
        "pdf_url": pdf_url
    }, indent=2)

paper_downloader_agent = Agent(
    role="Academic Paper Retriever",
    goal="Retrieve and download academic paper PDFs using DOI or URLs",
    backstory="""
You are a digital archivist specialized in locating downloadable
versions of academic papers.

You consult multiple academic databases such as Crossref, Unpaywall,
and arXiv to find legitimate PDF sources.

You NEVER invent URLs.
You ONLY use tool outputs.
""",
    tools=[
        resolve_doi,
        query_crossref_by_doi,
        query_unpaywall,
        query_arxiv,
        find_pdf_link,
        download_pdf
    ],
    llm=config.llm,
    verbose=True,
    max_iter=5,
    allow_delegation=False
)

def create_download_task(identifier: str) -> Task:
    return Task(
        description=f"""
You received an identifier for an academic paper.

IDENTIFIER:
\"\"\"
{identifier}
\"\"\"

The identifier may be:
- DOI
- URL
- arXiv ID
- Direct PDF link

STEPS:

1. If DOI, query Crossref for metadata
2. Query Unpaywall to find open access versions
3. If arXiv ID is available, use query_arxiv
4. If a PDF link is found, download using download_pdf
5. If no PDF is available, return status "not_available"

RULES:
- Only use links returned by tools
- Never invent URLs
- Prefer open access PDFs

OUTPUT JSON:
{{
  "identifier": "input",
  "status": "downloaded | not_available | failed",
  "file_path": "local path or null"
}}
""",
        agent=paper_downloader_agent,
        expected_output="JSON result with download status"
    )
