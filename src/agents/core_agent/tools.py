##### HARDCODED BY NOW #####

# === TOOLS FOR CORE AGENT ===

from langchain_community.document_loaders import PyPDFLoader
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_qdrant import QdrantVectorStore
from langchain_text_splitters import RecursiveCharacterTextSplitter
from qdrant_client import QdrantClient

import os

from crewai.tools import tool
from crewai import Crew, Task
import json
from src.entities.config import SystemConfig
config = SystemConfig()

# Import specialized agents
from src.agents.reference_agent import reference_finder_agent, create_reference_task
from src.agents.bibtex_agent import bibtex_generator_agent, create_bibtex_task
from src.agents.validator_agent import reference_validator_agent, create_validation_task
from src.agents.rag_agent import rag_agent, create_rag_task
from src.agents.governance_agent.governance_agent import GovAgent

from src.utils import plan_guardrail

gov_agent = GovAgent()

import json
from pathlib import Path
from datetime import datetime
from typing import Dict

@tool
def save_plan(plan_json:Dict) -> str:
    """
    Save a plan JSON to a .pln file.

    Args:
        plan_json (dict | str): The plan as a Python dict or JSON string.
    Returns:
        Path: Path to the saved .pln file.
    """

    directory = "plans"
    try:
        plan_data = plan_guardrail(plan_json)
    except Exception as e:
        return str({"error": e.args})

    Path(directory).mkdir(parents=True, exist_ok=True)

    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    file_path = Path(directory) / f"plan_{timestamp}.pln"

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(plan_data, f, indent=2, ensure_ascii=False)

    return "OK"



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
    Delegate to the Reference Validator Agent to validate data quality. It can validate any informtion of the reference, as the bibtex, authors, year.
    
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
def delegate_to_governance_plan(plan_json:str) -> str:
    """
    Delegate to the Governance Agent to validate a plan.
    
    Args:
        plan: JSON string with execution plan or other information to validate
        
    Returns:
        JSON string with governance validation report
    """
    print(f"\n[CORE] Delegating to Governance Agent...\n")

    try:
        plan_json = plan_guardrail(plan_json)
    except Exception as e:
        return str({"error": e.args})
    
    try:
        result = gov_agent.call_plan_validation_task(plan_json)
        return str(result)
    except Exception as e:
        return json.dumps({
            "status": "error",
            "message": f"Governance validation failed: {e}"
        })
    
@tool
def delegate_to_governance_execution(information: str) -> str:
    """
    Delegate to the Governance Agent to validate informations.
    
    Args:
        information: A string with some information to validate
        
    Returns:
        JSON string with governance validation report
    """
    print(f"\n[CORE] Delegating to Governance Agent...\n")

    information = str(information)
    
    try:
        result = gov_agent.call_execution_validation_task(information)
        return str(result)
    except Exception as e:
        return json.dumps({
            "status": "error",
            "message": f"Governance validation failed: {e}"
        })
    


from typing import List

@tool
def retrieve_agents() -> List[str]:
    """Returns list of available agent names in the system."""
    return ['reference_finder', 'bibtex_generator', 'governance', 'reference_validator', 'rag_agent']

@tool
def get_tools() -> List[str]:
    """Returns list of available tools names in the system."""
    return ['delegate_to_bibtex_generator','delegate_to_governance', 'delegate_to_reference_finder', 'delegate_to_validator', 'delegate_to_rag_agent']

SYSTEM_COLLECTION = "system_memory"

qdrant_client = QdrantClient(host="localhost", port=6333)
embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
)

@tool
def save_pdf_to_system_memory(pdf_path: str) -> str:
    """
    Extract text from a PDF and persist into system Qdrant collection.
    """

    if not os.path.exists(pdf_path):
        return json.dumps({"status": "error", "message": "File not found"})

    loader = PyPDFLoader(pdf_path)
    documents = loader.load()

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200
    )
    chunks = splitter.split_documents(documents)

    QdrantVectorStore.from_documents(
        documents=chunks,
        embedding=embeddings,
        url="http://localhost:6333",
        collection_name=SYSTEM_COLLECTION
    )

    return json.dumps({
        "status": "stored",
        "collection": SYSTEM_COLLECTION,
        "chunks_indexed": len(chunks)
    })

@tool
def delegate_to_rag_agent(query: str, paper_identifier:str) -> str:
    """
    Delegate to the Rag Agent to search for some information inside some paper.
    
    Args:
        query: a string with the data that you want from the paper.
        paper_identifier: a string with the name, or some other identifier of the paper
        
    Returns:
        JSON string with paper metadata
    """
    print(f"\n[CORE] Delegating to Rag agent...")
    print(f"[CORE] Reference: {query[:100]}...\n")
    
    task = create_rag_task(user_query=query, paper_identifier=paper_identifier)
    
    crew = Crew(
        agents=[rag_agent],
        tasks=[task],
        verbose=True,
    )
    
    try:
        result = crew.kickoff()
        return str(result)
    except Exception as e:
        return json.dumps({
            "status": "error",
            "message": f"Reference Finder failed: {e}"
        })
