from crewai import Agent, Task, Crew, Process
from src.entities.config import SystemConfig
from src.utils import split_references
import json
from src.agents.core_agent.tools import delegate_to_bibtex_generator,delegate_to_governance_execution, delegate_to_governance_plan, delegate_to_reference_finder, delegate_to_validator, save_plan, retrieve_agents, get_tools


from crewai import Agent

class CoreAgent:
    def __init__(self):

        config = SystemConfig()

        self.plan_output = config
        self.availiable_agents = config.avaliable_agents
        self.llm = config.llm
        self.verbose = config.verbose
        self.max_iterations = config.max_iterations

        self.core_orchestrator_agent = None

        self._setup_agent()

    def _setup_agent(self):

        self.core_orchestrator_agent = Agent(
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
                delegate_to_governance_execution,
                delegate_to_governance_plan,
                save_plan,
                retrieve_agents,
                get_tools
            ],
            llm=self.llm,
            max_iter=self.max_iterations,
            verbose=self.verbose,
        )


    def _orchestrate_plan(self, user_input: str):
        plan_and_validate_task = Task(
            description="""
            You are an orchestrator agent that MUST follow these instructions EXACTLY IN ORDER:

            1. Retrieve which agents you have available to include in the plan using the tool: 'retrieve_agents' (you can only include agents that you have available in the plan).
            2. Create an execution plan in valid JSON format for the user request.
            3. Use the tool 'delegate_to_governance' to validate the plan JSON string.
            4. If the validation fails, revise the plan and repeat step 3 until approved.
            5. Once approved, immediately use the tool 'save_plan' with:

            CRITICAL RULES:
            - Return a final answer ONLY after execute all steps defined above
            - DO NOT write any explanations, comments, or text responses
            - DO NOT execute any plan actions
            - DO NOT return any text output
            - You MUST complete by calling 'save_plan' tool
            - ONLY save the plan after validated
            - The execution plan MUST strictly follow this JSON schema:

                {
                    "plan_json": {
                        "plan": [
                            {
                                "agent": "the agent responsible",
                                "action": "the action that must be done",
                            }
                        ]
                    }
                }

                Plan rules:
                - The top-level key MUST be named "plan_json"
                - "plan" MUST be a JSON array
                - Do not add any other top-level keys

            """
            f"""
            USER REQUEST: {user_input}
            """,
            expected_output="A validated and saved execution plan JSON",
            agent=self.core_orchestrator_agent,
            tools=[retrieve_agents, delegate_to_governance_plan, save_plan],
        )

        crew = Crew(
            agents=[self.core_orchestrator_agent],
            tasks=[plan_and_validate_task],
            verbose=self.verbose,
        )

        result = crew.kickoff()
        return result

    def _orchestrate_execution(self, user_input:str, plan:str):
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
            agent=self.core_orchestrator_agent,
            tools=[
                get_tools,
                delegate_to_reference_finder,
                delegate_to_bibtex_generator,
                delegate_to_validator,
                delegate_to_governance_execution
            ],
        )

        crew = Crew(
            agents=[self.core_orchestrator_agent],
            tasks=[execute_plan_task],
            verbose=self.verbose,
            process=Process.sequential,
        )

        return crew.kickoff()


    def orchestrate(self, user_input: str):
        plan = self._orchestrate_plan(user_input)
        result = self._orchestrate_execution(user_input, plan)
        return result
