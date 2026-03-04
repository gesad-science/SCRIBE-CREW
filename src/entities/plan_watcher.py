import os
import json


class PlanWatcher:

    def __init__(self, plans_directory: str):
        self.plans_directory = plans_directory
        self.existant_plans = []
        self.plan = None

    # -----------------------------
    # 1. Carregar planos existentes
    # -----------------------------
    def scan_existing_plans(self):
        """
        Escaneia a pasta e armazena todos os arquivos .pln
        """
        self.existant_plans = [
            file
            for file in os.listdir(self.plans_directory)
            if file.endswith(".pln")
        ]

    # -----------------------------
    # 2. Detectar novo plano
    # -----------------------------
    def detect_new_plan(self):
        """
        Verifica se existe um novo arquivo .pln.
        Se existir, lê, transforma em JSON e salva em self.plan.
        """

        current_files = [
            file
            for file in os.listdir(self.plans_directory)
            if file.endswith(".pln")
        ]

        new_files = list(set(current_files) - set(self.existant_plans))

        if not new_files:
            return None

        # Se houver múltiplos, pega o primeiro detectado
        new_file = new_files[0]
        full_path = os.path.join(self.plans_directory, new_file)

        with open(full_path, "r", encoding="utf-8") as f:
            content = f.read()

        try:
            self.plan = json.loads(content)
        except json.JSONDecodeError as e:
            raise ValueError(f"O arquivo {new_file} não contém JSON válido.") from e

        # Atualiza memória interna
        self.existant_plans.append(new_file)

        return self.plan
