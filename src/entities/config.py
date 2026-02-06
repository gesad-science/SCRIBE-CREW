import yaml
from pathlib import Path
from crewai import LLM

from dotenv import load_dotenv

import os


class SystemConfig:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(SystemConfig, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if getattr(self, "_initialized", False):
            return
        self._initialized = True

        config = self._load_config_from_yaml('config.yaml')

        self.llm = None

        self.use_ollama = config['USE_OLLAMA']
        self.model = config['MODEL']
        self.timeout = config['TIMEOUT']
        self.temperature = config['TEMPERATURE']
        self.max_retries = config['MAX_RETRIES']
        self.max_iterations = config['MAX_ITERATIONS']
        self.verbose = config['VERBOSE']
        self.output_log_file = config.get('LOG_OUTPUT', False)

        self.avaliable_agents = config['CORE_CONFIG']['AVALIABLE_AGENTS']
        self.plan_output = config['CORE_CONFIG']['PLAN_OUTPUT']

        self.policies = config['GOVERNANCE_CONFIG']['POLICIES']

        self._setup_llm()

        if self.use_ollama is True:
            self._validate_ollama_connection()



    def _load_config_from_yaml(self, file_path: Path) -> dict:
        with open(file_path, "r") as file:
            return yaml.safe_load(file)

    def _validate_ollama_connection(self):
        """Test if Ollama is responding"""
        try:
            import requests
            response = requests.get("http://localhost:11434/api/tags", timeout=5)
            if response.status_code != 200:
                raise RuntimeError(f"Ollama returned status {response.status_code}")
            return True
        except requests.exceptions.ConnectionError:
            raise RuntimeError(
                "Cannot connect to Ollama. Make sure it's running:\n"
                "  $ ollama serve\n"
                "  $ ollama pull llama3.2:3b"
            )
        except Exception as e:
            raise RuntimeError(f"Ollama connection error: {e}")


    def _load_key(self):
        load_dotenv()
        return os.environ.get("API_KEY")


    def _setup_llm(self):
        if self.use_ollama is True:
            self.llm = LLM(
                model=f"ollama/{self.model}",
                base_url='http://localhost:11434',
                timeout=self.timeout,
                temperature=self.temperature,
                max_retries=self.max_retries,
            )
        else:
            self.llm = LLM(
                model=self.model,
                timeout=self.timeout,
                temperature=self.temperature,
                max_retries=self.max_retries,
                api_key=self._load_key()
            )
