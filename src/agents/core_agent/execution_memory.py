from dataclasses import asdict
from typing import Dict, List, Optional
from crewai.memory.memory import Memory
from qdrant_client import QdrantClient
from langchain_huggingface import HuggingFaceEmbeddings
from qdrant_client.http import models as rest
from langchain_qdrant import QdrantVectorStore
from langchain_core.documents import Document
import uuid
import json
from src.entities.execution import Execution


class ExecutionMemory:

    SIMILARITY_THRESHOLD = 0.30

    def __init__(self):
        self.client = QdrantClient(host="localhost", port=6333)

        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
        )

        self.collection = "execution_memory"
        self.embedding_size = 384

        self.ensure_collection()
        self.vector_store = QdrantVectorStore(
            client=self.client,
            collection_name=self.collection,
            embedding=self.embeddings
        )



    def ensure_collection(self):
        collections = self.client.get_collections().collections
        existing_names = [c.name for c in collections]

        if self.collection not in existing_names:
            self.client.create_collection(
                collection_name=self.collection,
                vectors_config=rest.VectorParams(
                    size=self.embedding_size,
                    distance=rest.Distance.COSINE
                ),
            )


    def save_execution(self, execution:Execution):

        document = Document(
            page_content=execution.input,
            metadata={
                "execution_id": str(uuid.uuid4()),
                "input": execution.input,
                "plan": execution.plan,
                "output": execution.output,
                "human_feedback": execution.human_feedback
            }
        )

        self.vector_store.add_documents([document])
        print(f"EXECUTION SAVED: {execution}")


    def search_similar(self, query: str, k: int = 5) -> List[Document]:


        results = self.vector_store.similarity_search_with_score(query, k=k)

        filtered = [
            doc for doc, distance in results
            if distance <= self.SIMILARITY_THRESHOLD
        ]

        return filtered

    def retrieve_reusable_plan(self, query: str) -> Optional[Dict]:


        similar_docs = self.search_similar(query)

        if not similar_docs:
            return None

        for doc in similar_docs:
            if doc.metadata.get("human_feedback"):
                return doc.metadata.get("plan")

        return similar_docs[0].metadata.get("plan")

    def rag(self, query: str) -> Dict:

        similar_docs = self.search_similar(query)

        if not similar_docs:
            return {
                "status": "no_match",
                "memory_source": self.collection,
                "chunks": []
            }

        return {
            "status": "success",
            "memory_source": self.collection,
            "chunks": [
                {
                    "content": doc.page_content,
                    "metadata": doc.metadata
                }
                for doc in similar_docs
            ]
        }
