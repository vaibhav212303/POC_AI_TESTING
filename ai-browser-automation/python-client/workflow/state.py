from dataclasses import dataclass, field
from typing import List

@dataclass
class WorkflowContext:
    # The list of steps (e.g., "Click Login", "Type Password")
    steps_queue: List[str] = field(default_factory=list)
    
    # Tracking execution
    current_step_index: int = 0
    failed: bool = False
    error_message: str = ""
    
    def mark_failed(self, error: str):
        self.failed = True
        self.error_message = error