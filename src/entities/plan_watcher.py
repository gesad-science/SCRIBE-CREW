import os
import json


class PlanWatcher:

    def __init__(self, plans_directory: str):
        self.plans_directory = plans_directory
        self.existant_plans = []
        self.plan = None

    def scan_existing_plans(self):

        self.existant_plans = [
            file
            for file in os.listdir(self.plans_directory)
            if file.endswith(".pln")
        ]
    def detect_new_plan(self):


        current_files = [
            file
            for file in os.listdir(self.plans_directory)
            if file.endswith(".pln")
        ]

        new_files = list(set(current_files) - set(self.existant_plans))

        if not new_files:
            return None

        new_file = new_files[0]
        full_path = os.path.join(self.plans_directory, new_file)

        with open(full_path, "r", encoding="utf-8") as f:
            content = f.read()

        try:
            self.plan = json.loads(content)
        except json.JSONDecodeError as e:
            raise ValueError(f"O arquivo {new_file} não contém JSON válido.") from e

        self.existant_plans.append(new_file)

        return self.plan
