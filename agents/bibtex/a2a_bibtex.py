import json
import uvicorn

from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentCapabilities, AgentCard, AgentInterface, AgentSkill

from crewai import Crew

from src.agents.bibtex_agent import (
    bibtex_generator_agent,
    create_bibtex_task
)


from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.utils import new_agent_text_message


class BibTeXGeneratorExecutor(AgentExecutor):
    async def execute(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:
        try:
            message = context.message
            part = message.parts[0]

            if hasattr(part, "text"):
                reference_text = part.text
            elif hasattr(part, "data"):
                reference_text = part.data
            else:
                reference_text = str(part)

            if not reference_text:
                await event_queue.enqueue_event(
                    new_agent_text_message("Error: Missing 'reference_text'")
                )
                return

            print("\n[A2A] Delegating to Bibtex Generator...")
            print(f"[A2A] Input: {reference_text[:100]}...\n")

            task = create_bibtex_task(reference_text=reference_text)

            crew = Crew(
                agents=[bibtex_generator_agent],
                tasks=[task],
                verbose=True,
            )

            result = crew.kickoff()

            await event_queue.enqueue_event(new_agent_text_message(str(result)))

        except Exception as e:
            await event_queue.enqueue_event(
                new_agent_text_message(f"Error: Bibtex Generator failed: {e}")
            )

    async def cancel(self, context, event_queue):
        raise Exception("Cancel not supported")



bibtex_skill = AgentSkill(
    id="bibtex_generator",
    name="Generate BibTeX entry",
    description="""
Delegate to the Bibtex Generator Agent to search for a paper.
Use this agent when you need to find the metadata of a paper given a reference string,
which can be a citation, bibliography entry, or partial name.
Returns metadata such as title, authors, year, url, and bibtex.
""",
    tags=["papers", "academic", "search", "reference"],
    examples=[
        "Attention is all you need",
        "Vaswani et al. 2017 transformer paper",
        "Find papers about LLMs in 2023"
    ],
)


agent_card = AgentCard(
    name="Bibtex Generator Agent",
    description="Find and retrieve metadata for academic papers from references",
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
            url="http://0.0.0.0:9995",
            transport="HTTP"
        )
    ],
    url="http://0.0.0.0:9995",
    skills=[bibtex_skill],
)


request_handler = DefaultRequestHandler(
    agent_executor=BibTeXGeneratorExecutor(),
    task_store=InMemoryTaskStore(),
)


app = A2AStarletteApplication(
    agent_card=agent_card,
    http_handler=request_handler,
)

if __name__ == "__main__":
    uvicorn.run(app.build(), host="0.0.0.0", port=9995)
