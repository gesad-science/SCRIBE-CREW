import json
import uvicorn

from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentCapabilities, AgentCard, AgentInterface, AgentSkill

from crewai import Crew

from src.agents.rag_agent import (
    rag_agent,
    create_rag_task
)


from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.utils import new_agent_text_message


class RAGExecutor(AgentExecutor):
    async def execute(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:
        try:
            message = context.message
            part = message.parts[0]

            if hasattr(part, "text"):
                user_query = part.text
            elif hasattr(part, "data"):
                user_query = part.data
            else:
                user_query = str(part)

            if not user_query:
                await event_queue.enqueue_event(
                    new_agent_text_message("Error: Missing 'query'")
                )
                return

            print("\n[A2A] Delegating to RAG Agent...")
            print(f"[A2A] Query: {user_query}\n")

            task = create_rag_task(user_query=user_query)

            crew = Crew(
                agents=[rag_agent],
                tasks=[task],
                verbose=True,
            )

            result = crew.kickoff()

            await event_queue.enqueue_event(new_agent_text_message(str(result)))

        except Exception as e:
            await event_queue.enqueue_event(
                new_agent_text_message(f"Error: RAG Agent failed: {e}")
            )

    async def cancel(self, context, event_queue):
        raise Exception("Cancel not supported")



rag_skill = AgentSkill(
    id="hierarchical_rag",
    name="Answer questions from hierarchical memory",
    description="""
Use this agent to answer questions about academic papers using internal memory.

The agent:
- Searches private memory first
- Falls back to system memory
- Caches results automatically

Strictly grounded responses:
- No hallucinations
- Only retrieved chunks are used
- Returns cited excerpts

If no information is found, returns 'not_found'.
""",
    tags=["rag", "memory", "qa", "papers"],
    examples=[
        "What does the paper say about transformers?",
        "Explain the methodology used in this study",
        "What are the main contributions of the paper?",
        "Summarize the results section"
    ],
)


agent_card = AgentCard(
    name="Hierarchical RAG Agent",
    description="Answer questions using private and system memory with strict grounding",
    version="1.0.0",
    default_input_modes=["text"],
    default_output_modes=["text"],
    capabilities=AgentCapabilities(
        streaming=False,
        extended_agent_card=False
    ),
    supported_interfaces=[
        AgentInterface(
            protocol_binding="JSONRPC",
            url="http://0.0.0.0:9997",
            transport="HTTP"
        )
    ],
    url="http://0.0.0.0:9997",
    skills=[rag_skill],
)


request_handler = DefaultRequestHandler(
    agent_executor=RAGExecutor(),
    task_store=InMemoryTaskStore(),
)


app = A2AStarletteApplication(
    agent_card=agent_card,
    http_handler=request_handler,
)

if __name__ == "__main__":
    uvicorn.run(app.build(), host="0.0.0.0", port=9997)
