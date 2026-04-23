import json
import uvicorn

from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentCapabilities, AgentCard, AgentInterface, AgentSkill

from crewai import Crew

from src.agents.reference_agent import (
    reference_finder_agent,
    create_reference_task
)


from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.utils import new_agent_text_message


class ReferenceFinderExecutor(AgentExecutor):

    async def execute(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:
        try:

            message = context.message
            part = message.parts[0]

            if hasattr(part, "text"):
                text = part.text
            elif hasattr(part, "data"):
                text = part.data
            else:
                text = str(part)

            print(f"\n[A2A] Input: {text[:100]}...\n")


            task = create_reference_task(reference_text=text)

            crew = Crew(
                agents=[reference_finder_agent],
                tasks=[task],
                verbose=True,
            )

            result = crew.kickoff()


            await event_queue.enqueue_event(
                new_agent_text_message(str(result))
            )

        except Exception as e:
            await event_queue.enqueue_event(
                new_agent_text_message(f"Error: {str(e)}")
            )

    async def cancel(self, context, event_queue):
        raise Exception("Cancel not supported")


reference_skill = AgentSkill(
    id="reference_finder",
    name="Find academic paper metadata",
    description="""
Delegate to the Reference Finder Agent to search for a paper.
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
    name="Reference Finder Agent",
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
            url="http://0.0.0.0:9998",
            transport="HTTP"
        )
    ],
    url="http://0.0.0.0:9998",
    skills=[reference_skill],
)


request_handler = DefaultRequestHandler(
    agent_executor=ReferenceFinderExecutor(),
    task_store=InMemoryTaskStore(),
)


app = A2AStarletteApplication(
    agent_card=agent_card,
    http_handler=request_handler,
)

if __name__ == "__main__":
    uvicorn.run(app.build(), host="0.0.0.0", port=9998)
