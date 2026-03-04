from src.agents.core_agent.core_agent import CoreAgent
from src.entities.execution import Execution
from src.agents.core_agent.execution_memory import ExecutionMemory
from src.entities.plan_watcher import PlanWatcher

def run_execution(core:CoreAgent, user_input:str):
    result = core.orchestrate(user_input=user_input)
    return result.raw

def run_execution_feedback(core:CoreAgent, memory:ExecutionMemory, plan_watcher:PlanWatcher, user_input:str):
    plan_watcher.scan_existing_plans()
    result = core.orchestrate(user_input=user_input).raw
    plan = plan_watcher.detect_new_plan()
    feedback = bool(input("Feedback"))
    exec = Execution()
    exec.input=user_input
    exec.plan = plan
    exec.output = result
    exec.human_feedback=feedback
    memory.save_execution(exec)
    return result
