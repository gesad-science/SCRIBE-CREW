from crewai import Agent, Task, Crew, Process
from src.entities.config import SystemConfig
config = SystemConfig()
from src.utils import split_references
import json
from src.agents.core_agent.tools import delegate_to_bibtex_generator,delegate_to_governance, delegate_to_reference_finder, delegate_to_validator, save_plan, retrieve_agents, get_tools

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
        save_plan,
        retrieve_agents,
        get_tools
    ],
    llm=config.llm,
    max_iter=config.max_agent_iterations,
    verbose=config.verbose,
)


def orchestrate_plan(user_input: str):
    plan_and_validate_task = Task(
        description="""
You are an orchestrator agent that MUST follow these instructions EXACTLY:

1. Retrieve which agents you have available to include in the plan using the tool: 'retrieve_agents' (you can only include agents that you have available in the plan).
2. Create an execution plan in valid JSON format for the user request.
3. Convert the plan to a JSON string.
4. Use the tool 'delegate_to_governance' to validate the plan JSON string.
5. If the validation fails, revise the plan and repeat step 3 until approved.
6. Once approved, immediately use the tool 'save_plan' with:
   - plan_json: the validated plan JSON string
   - directory: "plans"

CRITICAL RULES:
- Return a final answer ONLY after execute all steps defined above
- DO NOT write any explanations, comments, or text responses
- DO NOT execute any plan actions
- DO NOT return any text output
- You MUST complete by calling 'save_plan' tool
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
        tools=[retrieve_agents, delegate_to_governance, save_plan],
    )

    crew = Crew(
        agents=[core_orchestrator_agent],
        tasks=[plan_and_validate_task],
        verbose=config.verbose,
    )

    result = crew.kickoff()
    return result

def orchestrate_execution(user_input:str, plan:str):
    execute_plan_task = Task(
        description=f"""
Execute the previously validated execution plan step by step.

PLAN:
{plan}

Steps:
1. Get your availiable tools with the tool 'get_tools'
2. Use delegation tools that you retrieve in the step 1 to execute each action strictly in order.
3. Use the appropriate tool for each responsible agent.
4. Collect the outputs of all tools.
5. Produce the final response to the user using only the collected outputs.

Rules:
- Return ONLY after call all the necessary tools and collect their outputs.
- Pass the necessary information as context to each tool.
- Your final objective is use the plan to respond to user request:
- Do NOT modify the plan.
- Do NOT revalidate the plan.
- Do NOT add extra information beyond what the user requested.

USER REQUEST: {user_input}

""",
        expected_output="The final answer to the user.",
        agent=core_orchestrator_agent,
        tools=[
            get_tools,
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
    result = orchestrate_execution(user_input, plan)
    return result
