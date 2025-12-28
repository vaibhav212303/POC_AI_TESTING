class WorkflowContext:
    def __init__(self):
        # Input Data
        self.steps_queue = []       # Steps loaded from Markdown
        # Execution Data (The missing part)
        self.recorded_history = []  # Stores successful actions (Selector, Value, Action)
        # State Flags
        self.failed = False
        self.error_message = None
        # Generated Artifacts
        self.test_name = "UnknownTest"
        self.pom_class_name = None
        self.pom_path = None
        self.spec_path = None

    def mark_failed(self, error):
        """Helper to mark the workflow as failed and stop execution."""
        self.failed = True
        self.error_message = error
        print(f"🛑 Workflow Failed: {error}")