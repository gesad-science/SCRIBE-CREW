from src.agents.core_agent.core_agent import CoreAgent

#from tests.template_test import run_tests_and_save_results
from src.entities.execution import Execution
from src.agents.core_agent.execution_memory import ExecutionMemory
from src.entities.plan_watcher import PlanWatcher


core = CoreAgent()
memory = ExecutionMemory()
plan_watcher = PlanWatcher(plans_directory='plans')
while True:
    plan_watcher.scan_existing_plans()

    user_input = input("USER INPUT: ")

    if user_input=='q':
        break

    result = core.orchestrate(user_input=user_input)
    print(f"\n\n RESULT: \n{result}\n")

    plan = plan_watcher.detect_new_plan()
    feedback = bool(input("Feedback"))

    exec = Execution()

    exec.input=user_input
    exec.plan = plan
    exec.output = result.raw
    exec.human_feedback=feedback


    memory.save_execution(exec)

#run_tests_and_save_results(core=core)
