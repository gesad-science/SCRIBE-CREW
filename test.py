from src.agents.core_agent.core_agent import CoreAgent

core = CoreAgent()

user_input = input("USER INPUT: ")

print(core.orchestrate(user_input=user_input))