import json
import uvicorn

from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentCapabilities, AgentCard, AgentInterface, AgentSkill

from crewai import Crew

from src.agents.download_agent import (
    paper_downloader_agent,
    create_download_task
)


from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.utils import new_agent_text_message


class PaperDownloaderExecutor(AgentExecutor):
    async def execute(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:
        try:
            message = context.message
            part = message.parts[0]

            if hasattr(part, "text"):
                identifier = part.text
            elif hasattr(part, "data"):
                identifier = part.data
            else:
                identifier = str(part)

            if not identifier:
                await event_queue.enqueue_event(
                    new_agent_text_message("Error: Missing 'identifier'")
                )
                return

            print("\n[A2A] Delegating to Paper Downloader...")
            print(f"[A2A] Input: {identifier}\n")

            task = create_download_task(identifier=identifier)

            crew = Crew(
                agents=[paper_downloader_agent],
                tasks=[task],
                verbose=True,
            )

            result = crew.kickoff()

            await event_queue.enqueue_event(new_agent_text_message(str(result)))

        except Exception as e:
            await event_queue.enqueue_event(
                new_agent_text_message(f"Error: Paper Downloader failed: {e}")
            )

    async def cancel(self, context, event_queue):
        raise Exception("Cancel not supported")



download_skill = AgentSkill(
    id="paper_downloader",
    name="Download academic paper",
    description="""
Delegate to the Paper Downloader Agent to retrieve and download academic papers.

Use this agent when you have:
- DOI
- URL
- arXiv ID
- Direct PDF link

The agent will attempt to locate and download the PDF using trusted sources
like Crossref, Unpaywall, and arXiv.

Returns download status and local file path.
""",
    tags=["papers", "download", "academic", "pdf"],
    examples=[
        "10.1145/3377811.3380364",
        "https://doi.org/10.1038/s41586-020-2649-2",
        "arxiv:1706.03762",
        "https://arxiv.org/abs/1706.03762"
    ],
)


agent_card = AgentCard(
    name="Paper Downloader Agent",
    description="Retrieve and download academic paper PDFs from DOI, URL, or arXiv",
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
            url="http://0.0.0.0:9996",
            transport="HTTP"
        )
    ],
    url="http://0.0.0.0:9996",
    skills=[download_skill],
)


request_handler = DefaultRequestHandler(
    agent_executor=PaperDownloaderExecutor(),
    task_store=InMemoryTaskStore(),
)


app = A2AStarletteApplication(
    agent_card=agent_card,
    http_handler=request_handler,
)

if __name__ == "__main__":
    uvicorn.run(app.build(), host="0.0.0.0", port=9996)
