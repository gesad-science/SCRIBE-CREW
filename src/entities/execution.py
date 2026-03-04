from dataclasses import dataclass, field
from typing import Dict

@dataclass
class Execution:
    input: str = ''
    plan: Dict = field(default_factory=dict)
    output: str = ''
    human_feedback: bool = True
