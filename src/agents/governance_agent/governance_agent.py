from crewai import Agent, Task, Crew
from crewai.tools import tool
from src.entities.config import SystemConfig
from src.utils import safe_json_parse
import json
import re
from src.agents.governance_agent.tools import get_system_policies,validate_plan_structure,detect_pii,check_plan_efficiency

class GovAgent:
    def __init__(self):
        config = SystemConfig()

        self.llm = config.llm
        self.max_iter = config.max_iterations
        self.verbose = config.verbose

        self.governance_agent = None

        self._setup_agents()

    def _setup_agents(self):

        self.governance_agent = Agent(
            role="System Governance Controller",
            goal="Ensure all plans comply with policies and are well-structured",
            backstory="""
        You are the system's policy enforcement officer. You validate that all 
        execution plans follow the rules, are properly structured, contain no 
        sensitive information, and are efficient.

        You provide clear, constructive feedback when plans need improvement.
        You help maintain system integrity and data quality.
        """,
            tools=[
                get_system_policies,
                validate_plan_structure,
                detect_pii,
                check_plan_efficiency
            ],
            llm=self.llm,
            max_iter=self.max_iter,
            verbose=self.verbose,
            allow_delegation=False
        )


    def call_plan_validation_task(self, plan: str) -> str:
        task = Task(
            description=f"""
            You received content that needs governance validation:

            CONTENT:
            {plan}

            Your job is to thoroughly validate this content against system policies.

            VALIDATION STEPS:
            1. Use 'get_system_policies' to retrieve current policies
            2. Use 'validate_plan_structure' to check structure
            3. Use 'detect_pii' to scan for sensitive information
            4. Use 'check_plan_efficiency' to analyze efficiency

            PROVIDE A COMPREHENSIVE REPORT:
            - Whether the content is approved or rejected
            - List of policy violations (if any)
            - List of structural issues (if any)
            - PII detection results
            - Efficiency recommendations

            OUTPUT FORMAT (JSON):
            {{
            "approved": true/false,
            "status": "approved" or "rejected" or "needs_revision",
            "policy_violations": ["violation1", "violation2"],
            "structural_issues": ["issue1", "issue2"],
            "pii_detected": true/false,
            "efficiency_score": "high" or "medium" or "low",
            "recommendations": ["rec1", "rec2"],
            "summary": "brief summary of validation"
            }}
            """,
            agent=self.governance_agent,
            tools=[get_system_policies, validate_plan_structure, detect_pii, check_plan_efficiency],
            expected_output="A comprehensive governance validation report in JSON format"
        )

        crew = Crew(
        agents=[self.governance_agent],
        tasks=[task],
        verbose=self.verbose,
        )
        
        return crew.kickoff()
    
    def call_execution_validation_task(self, data:str) -> str:
        task = Task(
            description=f"""
            You received content that needs governance validation:

            CONTENT:
            {data}

            Your job is to thoroughly validate this content against system policies.

            VALIDATION STEPS:
            1. Use 'get_system_policies' to retrieve current policies
            2. Use 'detect_pii' to scan for sensitive information

            PROVIDE A COMPREHENSIVE REPORT:
            - Whether the content is approved or rejected
            - List of policy violations (if any)
            - List of structural issues (if any)
            - PII detection results
            - Efficiency recommendations

            OUTPUT FORMAT (JSON):
            {{
            "approved": true/false,
            "status": "approved" or "rejected" or "needs_revision",
            "policy_violations": ["violation1", "violation2"],
            "structural_issues": ["issue1", "issue2"],
            "pii_detected": true/false,
            "efficiency_score": "high" or "medium" or "low",
            "recommendations": ["rec1", "rec2"],
            "summary": "brief summary of validation"
            }}
            """,
            agent=self.governance_agent,
            tools=[get_system_policies, detect_pii],
            expected_output="A comprehensive governance validation report in JSON format"
        )

        crew = Crew(
        agents=[self.governance_agent],
        tasks=[task],
        verbose=self.verbose,
        )
        
        return crew.kickoff()