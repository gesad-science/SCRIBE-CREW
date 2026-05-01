import json
import uvicorn

from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentCapabilities, AgentCard, AgentInterface, AgentSkill

from crewai import Crew

from src.agents.validator_agent import (
    reference_validator_agent,
    create_validation_task
)


from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.utils import new_agent_text_message


class ReferenceValidatorExecutor(AgentExecutor):
    async def execute(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:
        try:
            message = context.message
            part = message.parts[0]

            if hasattr(part, "text"):
                raw = part.text
            elif hasattr(part, "data"):
                raw = part.data
            else:
                raw = str(part)

            if not raw:
                await event_queue.enqueue_event(
                    new_agent_text_message("Error: Missing 'reference_data'")
                )
                return

            if isinstance(raw, (dict, list)):
                reference_data = raw
            else:
                try:
                    reference_data = json.loads(raw)
                except Exception:
                    reference_data = raw

            print("\n[A2A] Delegating to Reference Validator...")
            try:
                preview = json.dumps(reference_data)[:200]
            except Exception:
                preview = str(reference_data)[:200]
            print(f"[A2A] Input: {preview}...\n")

            task = create_validation_task(reference_data=reference_data)

            crew = Crew(
                agents=[reference_validator_agent],
                tasks=[task],
                verbose=True,
            )

            result = crew.kickoff()

            await event_queue.enqueue_event(new_agent_text_message(str(result)))

        except Exception as e:
            await event_queue.enqueue_event(
                new_agent_text_message(f"Error: Reference Validator failed: {e}")
            )

    async def cancel(self, context, event_queue):
        raise Exception("Cancel not supported")



validation_skill = AgentSkill(
    id="reference_validation",
    name="Validate academic reference",
    description="""
Use this agent to validate academic reference data including metadata and BibTeX.

The agent performs:
- Metadata completeness validation (title, authors, year)
- BibTeX format validation
- Consistency checks between metadata and BibTeX

Returns a structured validation report with:
- Critical issues
- Warnings
- Recommendations

Use when you need to ensure data quality before storage or usage.
""",
    tags=["validation", "bibtex", "metadata", "academic"],
    examples=[
        '{"title": "Attention is All You Need", "authors": ["Vaswani"], "year": 2017}',
        '{"metadata": {...}, "bibtex": "@article{...}"}'
    ],
)


agent_card = AgentCard(
    name="Reference Validator Agent",
    description="Validate metadata and BibTeX quality for academic references",
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
            url="http://0.0.0.0:9994",
            transport="HTTP"
        )
    ],
    url="http://0.0.0.0:9994",
    skills=[validation_skill],
)


request_handler = DefaultRequestHandler(
    agent_executor=ReferenceValidatorExecutor(),
    task_store=InMemoryTaskStore(),
)


app = A2AStarletteApplication(
    agent_card=agent_card,
    http_handler=request_handler,
)


if __name__ == "__main__":
    uvicorn.run(app.build(), host="0.0.0.0", port=9994)
