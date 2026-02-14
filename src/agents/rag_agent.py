from crewai import Agent, Task, LLM
from crewai.tools import tool
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from src.entities.config import SystemConfig
import json

config = SystemConfig()

# ===============================
# GLOBAL CONFIG
# ===============================

SYSTEM_COLLECTION = "system_memory"
RAG_COLLECTION = "rag_private_memory"

qdrant_client = QdrantClient(host="localhost", port=6333)
embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
)

# ===============================
# TOOL — SMART RETRIEVAL WITH DELIMITER
# ===============================

@tool
def smart_retrieve_with_delimiter(input_json: str) -> str:
    """
    Hierarchical retrieval with delimiter filtering.

    Expected input JSON:
    {
        "query": "what the user wants to know",
        "paper_identifier": "paper title or unique identifier"
    }
    """

    try:
        data = json.loads(input_json)
        query = data["query"]
        paper_identifier = data["paper_identifier"]
    except Exception as e:
        return json.dumps({"error": f"Invalid input format: {e}"})

    print(f"[TOOL] Smart retrieval for paper: {paper_identifier}")
    print(f"[TOOL] Query: {query}")

    metadata_filter = {
        "paper_identifier": paper_identifier
    }

    # ---------------------------
    # STEP 1 — Try private memory
    # ---------------------------

    private_store = QdrantVectorStore(
        client=qdrant_client,
        collection_name=RAG_COLLECTION,
        embeddings=embeddings
    )

    private_docs = private_store.similarity_search(
        query,
        k=5,
        filter=metadata_filter
    )

    if private_docs:
        return json.dumps({
            "status": "success",
            "memory_source": "private_memory",
            "chunks": [
                {
                    "content": doc.page_content,
                    "metadata": doc.metadata
                }
                for doc in private_docs
            ]
        }, indent=2, ensure_ascii=False)

    # ---------------------------
    # STEP 2 — Try system memory
    # ---------------------------

    system_store = QdrantVectorStore(
        client=qdrant_client,
        collection_name=SYSTEM_COLLECTION,
        embeddings=embeddings
    )

    system_docs = system_store.similarity_search(
        query,
        k=5,
        filter=metadata_filter
    )

    if not system_docs:
        return json.dumps({
            "status": "not_found",
            "chunks": []
        })

    # ---------------------------
    # STEP 3 — Cache into private memory
    # ---------------------------

    texts = [doc.page_content for doc in system_docs]

    metadatas = [
        {
            **doc.metadata,
            "paper_identifier": paper_identifier
        }
        for doc in system_docs
    ]

    QdrantVectorStore.from_texts(
        texts=texts,
        metadatas=metadatas,
        embedding=embeddings,
        url="http://localhost:6333",
        collection_name=RAG_COLLECTION
    )

    # ---------------------------
    # STEP 4 — Retrieve again from private
    # ---------------------------

    refreshed_docs = private_store.similarity_search(
        query,
        k=5,
        filter=metadata_filter
    )

    return json.dumps({
        "status": "success",
        "memory_source": "system_memory_cached",
        "chunks": [
            {
                "content": doc.page_content,
                "metadata": doc.metadata
            }
            for doc in refreshed_docs
        ]
    }, indent=2, ensure_ascii=False)


# ===============================
# AGENT
# ===============================

rag_agent = Agent(
    role="Hierarchical RAG Specialist",
    goal="Answer user questions using hierarchical memory filtered by paper identifier",
    backstory="""
You operate with hierarchical memory:

1. Private memory (filtered by paper identifier)
2. System memory (read-only, filtered by paper identifier)

You must:
- Use smart_retrieve_with_delimiter ONCE.
- Answer strictly from retrieved chunks.
- Never
hallucinate.
- If not_found, return not_found.
""",
    tools=[smart_retrieve_with_delimiter],
    llm=config.llm,
    max_iter=2,
    verbose=True,
    allow_delegation=False
)


# ===============================
# TASK BUILDER
# ===============================

def create_rag_task(user_query: str, paper_identifier: str) -> Task:

    input_payload = json.dumps({
        "query": user_query,
        "paper_identifier": paper_identifier
    })

    return Task(
        description=f"""
You received a question about a specific paper.

PAPER IDENTIFIER:
\"\"\"
{paper_identifier}
\"\"\"

USER QUESTION:
\"\"\"
{user_query}
\"\"\"

STEPS:
1. Use 'smart_retrieve_with_delimiter' ONCE with this JSON:
{input_payload}

2. If status is "success":
   - Answer strictly using returned chunks.
3. If status is "not_found":
   - Return not_found.

IMPORTANT RULES:
- Do NOT use external knowledge.
- Do NOT invent content.
- Only rely on retrieved chunks.
- Cite excerpts used.

OUTPUT FORMAT (JSON):
{{
  "status": "answered" or "not_found",
  "memory_source": "...",
  "answer": "...",
  "sources_used": [
      {{
          "excerpt": "...",
          "metadata": "..."
      }}
  ]
}}
""",
        agent=rag_agent,
        expected_output="Grounded hierarchical RAG response"
    )