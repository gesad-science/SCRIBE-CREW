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
        self.otel_sdk_disabled = config['OTEL_SDK_DISABLED']
        self.crewai_telemetry_disabled = config['CREWAI_TELEMETRY_ENABLED']

        self.use_ollama = config['USE_OLLAMA']
        self.model_url = config['MODEL_URL']

        self.model = config['MODEL']
        self.llm_timeout = config['LLM_TIMEOUT']
        self.core_agent_timeout = config['CORE_AGENT_TIMEOUT']
        self.reference_agent_timeout = config['REFERENCE_AGENT_TIMEOUT']
        self.bibtex_agent_timeout = config['BIBTEX_AGENT_TIMEOUT']
        self.validator_agent_timeout = config['VALIDATOR_AGENT_TIMEOUT']
        self.governance_agent_timeout = config['GOVERNANCE_AGENT_TIMEOUT']

        self.max_agent_iterations = config['MAX_AGENT_ITERATIONS']
        self.max_rpm = config['MAX_RPM']
        self.enable_memory = config['ENABLE_MEMORY']
        self.verbose = config['VERBOSE']

        self.semantic_scholar_user_agent = config['SEMANTIC_SCHOLAR_USER_AGENT']

        self.log_level = config['LOG_LEVEL']
        self.temperature = config['TEMPERATURE']

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
                base_url=self.model_url,
                timeout=self.llm_timeout,
                temperature=self.temperature,  
                max_retries=5,
            )
        else:
            self.llm = LLM(
                model=self.model,
                timeout=self.llm_timeout,
                temperature=self.temperature,  
                max_retries=5,
                api_key=self._load_key()
            )