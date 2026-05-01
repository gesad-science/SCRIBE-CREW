from langchain_community.document_loaders import PyPDFLoader
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_qdrant import QdrantVectorStore
from langchain_text_splitters import RecursiveCharacterTextSplitter
from qdrant_client import QdrantClient

from pydantic import BaseModel

import os
from typing import Type

from crewai.tools import tool
from crewai import Crew, Task
import json
from src.entities.config import SystemConfig
config = SystemConfig()

from src.agents.reference_agent import reference_finder_agent, create_reference_task
from src.agents.bibtex_agent import bibtex_generator_agent, create_bibtex_task
from src.agents.validator_agent import reference_validator_agent, create_validation_task
from src.agents.rag_agent import rag_agent, create_rag_task
from src.agents.download_agent import create_download_task, paper_downloader_agent
from src.agents.governance_agent.governance_agent import GovAgent
from src.agents.core_agent.execution_memory import ExecutionMemory
from src.entities.config import SystemConfig
from src.utils import plan_guardrail
import requests

gov_agent = GovAgent()
config = SystemConfig()
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List

from crewai.tools import BaseTool
from pydantic import BaseModel, Field

class PlanStep(BaseModel):
    agent: str
    action: str
    input: str

class PlanContainer(BaseModel):
    plan: List[PlanStep]

class SavePlanInput(BaseModel):
    plan_json: PlanContainer

class SavePlanTool(BaseTool):
    name: str = "save_plan"
    description: str = "Saves the validated plan"

    args_schema: Type[BaseModel] = SavePlanInput


    def _run(self, plan_json: dict) -> str:
        save_plan(plan_json=plan_json)

def save_plan(plan_json: Dict) -> str:
    """
    Save a plan.

    REQUIRED FORMAT:
    {
        "plan": [
            {"step": "description of step 1"},
            {"step": "description of step 2"}
        ]
    }

    Rules:
    - 'plan' MUST be a list
    - Each item MUST contain a 'step' field
    - Do NOT pass empty dict
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
    Use this agent when you need to find the metadata of a paper given a reference string, which can be a citation in the text, a bibliography entry, or any other string that contains information about the paper, as only the name. The Reference Finder Agent will try to extract as much information as possible from the input and return the paper metadata, such as title, authors, year, url, and bibtex.

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
        paper_metadata_json: JSON string with paper metadata (if no metadata is provided, the agent will try to find the metadata using any information it has in the context, like the title or authors)

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

class GovernancePlanInput(BaseModel):
    plan_json: PlanContainer

class DelegateToGovernancePlanTool(BaseTool):
    name: str = "delegate_to_governance"
    description: str = "Validate a plan using governance agent"

    args_schema: Type[BaseModel] = GovernancePlanInput

    def _run(self, plan_json: dict) -> str:
        print("\n[CORE] Delegating to Governance Agent...\n")

        try:
            # GARANTE formato correto
            if isinstance(plan_json, str):
                plan_json = json.loads(plan_json)

            validated = plan_guardrail(plan_json)

            result = gov_agent.call_plan_validation_task(validated)

            return json.dumps(result)

        except Exception as e:
            return json.dumps({
                "status": "error",
                "message": str(e)
            })
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
        print("GOVERNANCE VALIDATION RESULT 2:", result)
        return str(result)
    except Exception as e:
        return json.dumps({
            "status": "error",
            "message": f"Governance validation failed: {e}"
        })

@tool
def delegate_to_download_agent(paper_information: str) -> str:
    """
    Delegate to the Download Agent to download a PDF from a URL and store it in system memory.
    ALWAYS use this agent before RAG Agent when you need to find specific information inside the paper, as the Download Agent can give the RAG Agent access to the full text of the paper, which can be crucial to find the right answer for the user query.
    You should call this agent when the user asks for information that requires access to the full text of the paper, and you don't have it in your internal memory. If you don't have any of this information but you have other metadata like the title or authors, you can still call the Download Agent and it will try to find the PDF using that metadata.

    NOTES:
    ALWAYS after running this agent, you should call the "save_pdf_to_system_memory" tool to give the RAG Agent access to the paper content and be able to find the right answer for the user query.

    Args:
        paper_information: The URL of the PDF to download or doi/arxiv id to find the PDF. (if no information is provided, the agent should try to find the PDF using any information it has in the context, like the title or authors)
    """

    task = create_download_task(paper_information)

    crew = Crew(
        agents=[paper_downloader_agent],
        tasks=[task],
        verbose=True,
    )

    try:
        result = crew.kickoff()
        return str(result)
    except Exception as e:
        return json.dumps({
            "status": "error",
            "message": f"Download Agent failed: {e}"
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
import inspect


@tool
def retrieve_agents() -> str:
    """
    Returns metadata about explicitly allowed agent-delegation tools.
    """

    allowed_tools = [
        delegate_to_reference_finder,
        delegate_to_bibtex_generator,
        delegate_to_governance_execution,
        delegate_to_validator,
        delegate_to_download_agent,
        delegate_to_rag_agent,
    ]

    agents_metadata = []

    for tool_obj in allowed_tools:
        raw_docstring = inspect.getdoc(tool_obj.func)

        agents_metadata.append({
            "agent": tool_obj.name.replace("delegate_to_", ""),
            "tool_name": tool_obj.name,
            "description": raw_docstring
        })
    return json.dumps(agents_metadata, indent=2, ensure_ascii=False)


@tool
def get_tools() -> List[str]:
    """Returns list of available tools names in the system."""
    return ['delegate_to_bibtex_generator','delegate_to_governance', 'delegate_to_reference_finder', 'delegate_to_validator', 'delegate_to_rag_agent', 'delegate_to_download_agent']

SYSTEM_COLLECTION = "system_memory"

qdrant_client = QdrantClient(host=config.qdrant_host, port=6333)
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
        url=f"http://{config.qdrant_host}:6333",
        collection_name=SYSTEM_COLLECTION
    )

    return json.dumps({
        "status": "stored",
        "collection": SYSTEM_COLLECTION,
        "chunks_indexed": len(chunks)
    })

@tool
def delegate_to_rag_agent(query: str) -> str:
    """
    Delegate to the Rag Agent to search for some information inside some paper.
    This agent should be used when you need to find specific information inside the paper, and you don't have that information in your internal memory. You can provide any information you have about the paper, like the title, authors, year, or even the PDF path if you have it in the context, and the Rag Agent will try to find the answer for your query using all the information it has in the context and also searching inside the paper if it has access to it.

    NOTES:
    This agent only can find information inside some paper if the paper is in the system memory, so before calling this agent, ensure the paper is indexed in the system memory.

    Args:
        query: a string with the data that you want from the paper.

    Returns:
        JSON string with paper metadata
    """
    print(f"\n[CORE] Delegating to Rag agent...")
    print(f"[CORE] Reference: {query[:100]}...\n")

    task = create_rag_task(user_query=query)

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
@tool
def get_similar_plans(input: str) -> str:
    """
    Retrieve a previously validated execution plan that can be reusable for the given input.

    This function searches the execution memory for a plan that is semantically
    similar to the provided input and has already been validated.

    Args:
        input (str): The current user request or task description used to search
                     for a reusable execution plan.

    Returns:
        The reusable execution plan object if a similar validated plan is found.
        Returns the string 'Not found' if no reusable plan exists.

    Notes:
        - The similarity comparison logic is handled internally by ExecutionMemory.
        - This function does not generate new plans; it only retrieves existing ones.
    """
    try:
        memory = ExecutionMemory()
        usable_plan = memory.retrieve_reusable_plan(input)

        if usable_plan:
            return str(usable_plan)
        else:
            return 'Not found'

    except Exception as e:
        return json.dumps({
            "status": "error",
            "message": f"Error retrieving similar plans: {e}"
        })

@tool
def get_agents():
    """
    Return a detailed list with the available agents and their utilities
    """

    return retrieve_detailed_agents()


def retrieve_detailed_agents():

    try:
        response = requests.get("http://scribe-control-plane:7000/agents")
        return response.json()
    except Exception as e:
        return json.dumps({
            "status": "error",
            "message": f"Error connecting to control plane: {e}"
        })

@tool
def get_agent_names():
    """Returns a list of available agent names in the system."""
    agents = retrieve_detailed_agents()
    if isinstance(agents, dict) and "agents" in agents:
        agents = agents["agents"]
        return [agent["name"] for agent in agents]
    else:
        return []



@tool("call_agent")
def call_agent(agent_name: str, input_data:str) -> str:
    """
    Calls an available agent.

    Args:
        payload.agent_name: Name of the agent
        payload.input_data: Input data (string or dict)
    """

    try:
        response = requests.post(
            "http://scribe-control-plane:7000/call",
            json={
                "agent_name": agent_name,
                "input_data": input_data
            }
        )
        return response.json()
    except Exception as e:
        return json.dumps({
            "status": "error",
            "message": f"Error connecting to control plane: {e}"
        })
