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

from qdrant_client.http import models as rest

def ensure_collection(client, collection_name: str, embedding_size: int):
    collections = client.get_collections().collections
    existing_names = [c.name for c in collections]

    if collection_name not in existing_names:
        client.create_collection(
            collection_name=collection_name,
            vectors_config=rest.VectorParams(
                size=embedding_size,
                distance=rest.Distance.COSINE
            ),
        )


# ===============================
# TOOL — SMART RETRIEVAL WITH DELIMITER
# ===============================

@tool
def smart_retrieve_with_delimiter(query: str) -> str:
    """
    Hierarchical retrieval with delimiter filtering.

    Expected input JSON:
    {
        "query": "what the user wants to know in natural language",
    }
    """


    print(f"[TOOL] Query: {query}")

    SIMILARITY_THRESHOLD = 0.50  # ajuste empiricamente

    embedding_size = len(embeddings.embed_query("test"))
    ensure_collection(qdrant_client, RAG_COLLECTION, embedding_size)

    private_store = QdrantVectorStore(
        client=qdrant_client,
        collection_name=RAG_COLLECTION,
        embedding=embeddings
    )

    # ---------------------------
    # STEP 1 — Try private memory
    # ---------------------------

    private_results = private_store.similarity_search_with_score(
        query,
        k=5,
    )

    private_docs = [
        doc for doc, score in private_results
        if score >= SIMILARITY_THRESHOLD
    ]

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
        embedding=embeddings
    )

    system_results = system_store.similarity_search_with_score(
        query,
        k=5,
    )

    system_docs = [
        doc for doc, score in system_results
        if score >= SIMILARITY_THRESHOLD
    ]

    if not system_docs:
        return json.dumps({
            "status": "not_found",
            "chunks": []
        })

    # ---------------------------
    # STEP 3 — Cache into private memory
    # ---------------------------

    texts = [doc.page_content for doc in system_docs]
    metadatas = [doc.metadata for doc in system_docs]

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

    refreshed_results = private_store.similarity_search_with_score(
        query,
        k=5,
    )

    refreshed_docs = [
        doc for doc, score in refreshed_results
        if score >= SIMILARITY_THRESHOLD
    ]

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

def create_rag_task(user_query: str) -> Task:

    input_payload = json.dumps({
        "query": user_query,
    })

    return Task(
        description=f"""
You received a question about a specific paper.

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
