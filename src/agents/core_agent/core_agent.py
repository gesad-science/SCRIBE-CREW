from crewai import Agent, Task, Crew, Process
from src.entities.config import SystemConfig
config = SystemConfig()
from src.utils import split_references
import json
from src.agents.core_agent.tools import delegate_to_bibtex_generator,delegate_to_governance, delegate_to_reference_finder, delegate_to_validator, save_plan

from src.agents.governance_agent import governance_agent
# === CORE AGENT ===

from crewai import Agent

core_orchestrator_agent = Agent(
    role="Core Orchestrator Agent",
    goal="Coordinate specialized agents to fulfill academic reference requests",
    backstory="""
You are the system's core orchestrator.

You do not perform domain work yourself.
You coordinate specialized agents to plan and execute tasks.
You must always respect governance validation before any execution.
You can only act through the tools provided.
""",
    tools=[
        delegate_to_reference_finder,
        delegate_to_bibtex_generator,
        delegate_to_validator,
        delegate_to_governance,
        save_plan
    ],
    llm=config.llm,
    max_iter=config.max_agent_iterations,
    verbose=config.verbose,
)


def orchestrate_plan(user_input: str):
    plan_and_validate_task = Task(
        description="""
You are an orchestrator agent that MUST follow these instructions EXACTLY:

1. Create an execution plan in valid JSON format for the user request.
2. Convert the plan to a JSON string.
3. Use the tool 'delegate_to_governance' to validate the plan JSON string.
4. If the validation fails, revise the plan and repeat step 3 until approved.
5. Once approved, immediately use the tool 'save_plan' with:
   - plan_json: the validated plan JSON string
   - directory: "plans"

CRITICAL RULES:
- DO NOT write any explanations, comments, or text responses
- DO NOT execute any plan actions
- DO NOT return any text output
- You MUST complete by calling 'save_plan' tool
- Your only output should be tool calls
- The execution plan MUST strictly follow this JSON schema:

    {
    "plan": [
        {
        "agent": "the agent responsible",
        "action": "the action that must be done",
        }
    ]
    }

    Plan rules:
    - The top-level key MUST be named "plan"
    - "plan" MUST be a JSON array
    - Do not add any other top-level keys

"""
f"""
USER REQUEST: {user_input}
""",
        expected_output="A validated and saved execution plan JSON",
        agent=core_orchestrator_agent,
        tools=[delegate_to_governance, save_plan],
    )

    crew = Crew(
        agents=[core_orchestrator_agent],
        tasks=[plan_and_validate_task],
        verbose=config.verbose,
    )

    result = crew.kickoff()
    return result

def orchestrate_execution(plan):
    execute_plan_task = Task(
        description=f"""
Execute the previously validated execution plan step by step.

PLAN:
{plan}

Steps:
1. Load the approved plan.
2. Execute each action strictly in order.
3. Use the appropriate tool for each responsible agent.
4. Collect the outputs of all agents.
5. Produce the final response to the user using only the collected outputs.

Rules:
- Do NOT modify the plan.
- Do NOT revalidate the plan.
- Do NOT add extra information beyond what the user requested.
""",
        expected_output="The final answer to the user.",
        agent=core_orchestrator_agent,
        tools=[
            delegate_to_reference_finder,
            delegate_to_bibtex_generator,
            delegate_to_validator,
        ],
    )

    crew = Crew(
        agents=[core_orchestrator_agent],
        tasks=[execute_plan_task],
        verbose=config.verbose,
        process=Process.sequential,
    )

    return crew.kickoff()


def orchestrate(user_input: str):
    plan = orchestrate_plan(user_input)
    result = orchestrate_execution(plan)
    return result
