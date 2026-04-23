import os

#os.environ["CI"] = "true"
os.environ["CREWAI_TELEMETRY"] = "false"
os.environ["CREWAI_TELEMETRY_DISABLED"] = "true"
os.environ["CREWAI_TRACING_ENABLED"] = "false"

#os.environ["LANGCHAIN_TRACING_V2"] = "false"
os.environ["OTEL_SDK_DISABLED"] = "true"

from crewai import Agent, Task, Crew, Process
from src.entities.config import SystemConfig
from src.agents.core_agent.tools import (
                                         delegate_to_governance_plan,
                                         save_plan,
                                         save_pdf_to_system_memory,
                                         get_similar_plans,
                                         get_agents,
                                         call_agent,
                                         get_agent_names)


from crewai import Agent
from langchain_huggingface import HuggingFaceEmbeddings

from collections import deque

emb = HuggingFaceEmbeddings(
            model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
        )

class CoreAgent:
    def __init__(self):

        config = SystemConfig()

        self.plan_output = config
        self.availiable_agents = config.avaliable_agents
        self.llm = config.llm
        self.verbose = config.verbose
        self.max_iterations = config.max_iterations
        self.output_log_file = config.output_log_file
        self.core_orchestrator_agent = None
        self.crew=None

        self.ollama_host = config.ollama_host
        self.qdrant_host = config.qdrant_host

        self.conversation_window = deque(maxlen=5)

        self._setup_agent()
        self._setup_crew()


    def add_message(self, role, content):
        self.conversation_window.append({"role": role, "content": content})

    def get_recent_context(self):
        return list(self.conversation_window)

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
        You can only return the final output after executing all the necessary tasks in order.
        """,
            tools=[delegate_to_governance_plan, save_plan, save_pdf_to_system_memory, get_similar_plans, get_agents, call_agent, get_agent_names],
            llm=self.llm,
            max_iter=self.max_iterations,
            verbose=self.verbose,
        )


    def _plan_task(self):
        return Task(
            description="""
            You are an orchestrator agent that MUST follow these instructions EXACTLY IN ORDER:

            1. You should check if the user's request contains any directory paths that they want to use in the request. If it does, use tool 'save_pdf_to_system_memory', passing the path to save it in the system memory.
            2. Retrieve which agents you have available to include in the plan using the tool: 'get_agents' (you can only include agents that you have available in the plan).
            3. Create an execution plan in valid JSON format for the user request.
            4. You MUST use the tool 'delegate_to_governance' to validate the plan JSON string.
            5. If the validation fails, revise the plan and repeat step 3 until approved.
            6. ONLY if approved, immediately use the tool 'save_plan'
            7. After return the approved and saved plan immediately.

            CRITICAL RULES:
            - Return a final answer ONLY after execute all steps defined above
            - DO NOT write any explanations, comments, or text responses
            - DO NOT execute any plan actions
            - DO NOT return any text output
            - You MUST complete by calling 'save_plan' tool
            - ONLY save the plan after validated
            - If the governance agent returns a problem that is not related to the plan format, but rather to information that violates the system's business rules, forward this information and immediately skip to the post-execution task, as there should be no execution in such cases.
            - The execution plan MUST strictly follow this JSON schema:

                {
                    "plan_json": {
                        "plan": [
                            {
                                "agent": "the agent responsible",
                                "action": "the action that must be done",
                                "input": "the input that the responsible agent needs to perform the action"
                            }
                        ]
                    }
                }

                Plan rules:
                - The top-level key MUST be named "plan_json"
                - "plan" MUST be a JSON array
                - Do not add any other top-level keys

            """
            """
            USER REQUEST: {user_input}
            """,
            expected_output="A validated and saved execution plan JSON",
            agent=self.core_orchestrator_agent,
            tools=[get_agents, delegate_to_governance_plan, save_plan],
        )

    def _execution_task(self):
        return Task(
            description="""
            Execute the previously validated execution plan step by step.

            Steps:
            1. Get your availiable agents with the tool 'get_agent_names'
            2. Use tool 'call_agent' passing the name of the agents that you retrieve in the step 1 to execute each action strictly in order.
            3. Collect the outputs of all agents.
            4. Produce the final response to the user using only the collected outputs.

            Rules:
            - You MUST strictly follow the order of the steps in the plan.
            - Return ONLY after call all the necessary agents and collect their outputs.
            - You CAN'T RETURN before executing all the steps in the plan, even if some of them fail, as long as they are not critical to the execution of the other steps. In case of a failed step, you should collect the error message and include it in the final answer to the user, so they are aware of what went wrong.
            - Pass the necessary information as context to each agent.
            - Your final objective is use the plan to respond to user request.
            - Do NOT modify the plan.
            - Do NOT revalidate the plan.
            - Do NOT add extra information beyond what the user requested.
            - Make sure you are executing ALL the steps in the plan, and not leaving any step behind, as all steps are important to produce the final answer to the user.
            - Even if some step fails, you should keep executing the other steps, as long as the failed step is not critical to the execution of the other steps. In case of a failed step, you should collect the error message and include it in the final answer to the user, so they are aware of what went wrong.

            """,
            expected_output="The final answer to the user.",
            agent=self.core_orchestrator_agent,
            tools=[get_agent_names, call_agent],
        )

    def _pre_plan_task(self):
        return Task(
            description="""
            Before starting the execution phase, you MUST run a pre-execution pipeline.

            Your responsibilities in the pre-execution phase:

            1. Directory Path Detection
            - Analyze the user's request and detect any explicit directory path (absolute or relative).
            - If a directory path is found:
                - Call the tool `save_pdf_to_system_memory`
                - Pass the detected path exactly as provided by the user.
            - If no directory path is present, skip this step.

            2. Plan Reuse Verification
            - Before generating a new execution plan, call the tool `get_similar_plans`.
            - Provide the current user request as input.
            - If a validated similar plan exists in the database:
                - Verify that it can be reused for the current input.
                - If it is reusable, adapt it to the current request and return it. Otherwise, just proceed to the other tasks
            - If no similar validated plan is found:
                - Return Not Found Plan.

            - Important notes on plan reuse:
                - YOU ONLY RETURN SOMETHING IF THE TOOL `get_similar_plans` RETURNS A VALIDATED PLAN THAT CAN BE REUSED FOR THE CURRENT REQUEST.
                - You NEVER creates a new plan, only edit the retrieved plan if it is reusable.
                - You can edit some plan if it is an output of the tool `get_similar_plans`, else you MUST return Not Found Plan
                - You MUST adapt the retrieved plan if necessary to make it reusable for the CURRENT REQUEST and to the CURRENT CONTEXT.
                - Do not return a plan that is not adapted to the current context.
                - Ensure that the reused plan is edited and fully aligned with the current user request and context before returning it.
                - If the retrieved plan cannot be adapted for the current request, you MUST proceed to create a new plan as you would normally do, without returning the retrieved plan.

            This pre-execution pipeline must always be completed before any task execution begins.
            """,
            expected_output="A reusable plan or only a flag to keep going",
            agent=self.core_orchestrator_agent,
            tools=[save_pdf_to_system_memory, get_similar_plans]
        )

    def _context_understanding_task(self):
        return Task(
            description="""
            You are in a chatbot system. The current user request: ({user_input}) could be part of a broader conversation, so consider that the user could be referring to previous recent interactions or providing new information in the current request.

            Assemble the necessary context from the current user request and previous interactions in your memory to fully understand the user's needs and intentions before proceeding to the next steps.

            In addition, prioritize in your context understanding the last 5 messages: {recent_context}

            NOTES:
            - You cannot use any tool in this task, so you must rely solely on your ability to understand and process natural language to extract the necessary context.
            """,
            expected_output="A new user request enriched with the necessary context from previous interactions to be fully understood",
            agent=self.core_orchestrator_agent,
            tools=[]
        )

    def _post_execution_task(self):
        return Task(
            description="""
            After the execution of the plan, you MUST run a post-execution pipeline.

            Your responsibilities in the post-execution phase:
            1. Result format: Get the execution results data and format it in natural language in a clear and concise way to be returned to the user.
            2. Ensure information quality and quantity: Make sure to only return the necessary information to the user based on their request and the execution results. Avoid adding any unnecessary information that was not explicitly requested by the user.

            NOTES:
            - If the content of the execution suggests some kind of comparison or summary, add a table that summarizes or compares the results. The table should be in Markdown format:
            | Metric | Value |
            |--------|-------|
            |        |       |
            """,
            expected_output="A clear and concise natural language response to the user based on the execution results",
            agent=self.core_orchestrator_agent,
            tools=[]
        )

    def _setup_crew(self):
        context_understanding_task = self._context_understanding_task()
        pre_plan_task = self._pre_plan_task()
        plan_task = self._plan_task()
        execution_task = self._execution_task()
        post_execution_task = self._post_execution_task()

        print(f"ollama host: {self.ollama_host}")

        crew = Crew(
            agents=[self.core_orchestrator_agent],
            tasks=[context_understanding_task, pre_plan_task, plan_task, execution_task, post_execution_task],
            verbose=self.verbose,
            process=Process.sequential,
            output_log_file=self.output_log_file,
            memory=True,
            tracing=False,
            embedder={
            "provider": "ollama",
            "config": {
                "model_name": "nomic-embed-text",
                "url": f"{self.ollama_host}"
            }
        }
        )

        crew.reset_memories(command_type='all')
        self.crew=crew

    def orchestrate(self, user_input:str):
        self.add_message(role="user", content=user_input)
        return self.crew.kickoff(inputs={"user_input": user_input, "recent_context": self.get_recent_context()})
