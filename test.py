from src.agents.core_agent.core_agent import CoreAgent
import sys
from logs.utils import Tee

from tests.template_test import run_tests_and_save_results

log_file = open("system.log", "a", buffering=1)

sys.stdout = Tee(sys.__stdout__, log_file)
sys.stderr = Tee(sys.__stderr__, log_file)

core = CoreAgent()

#user_input = input("USER INPUT: ")

#print(core.orchestrate(user_input=user_input))

run_tests_and_save_results(core=core)

def restore_terminal_output():
    if sys.stdout != sys.__stdout__:
        sys.stdout.flush()
        if hasattr(sys.stdout, 'close'):
            sys.stdout.close()
        sys.stdout = sys.__stdout__
        return True
    return False

restore_terminal_output()
