import asyncio
from abc import ABC, abstractmethod
from workflow.state import WorkflowContext
from utils.file_parser import read_test_steps
from core.ai import get_ai_response

class BaseNode(ABC):
    @abstractmethod
    async def execute(self, context: WorkflowContext, session=None):
        pass

# --- NODE 1: LOAD STEPS FROM MARKDOWN ---
class FixtureLoaderNode(BaseNode):
    def __init__(self, file_path: str):
        self.file_path = file_path

    async def execute(self, context: WorkflowContext, session=None):
        print(f"📂 Loading Test Scenario: {self.file_path}")
        try:
            steps = read_test_steps(self.file_path)
            if not steps:
                raise ValueError("File is empty or contains no steps.")
            context.steps_queue = steps
            print(f"   ✅ Loaded {len(steps)} steps.")
        except Exception as e:
            context.mark_failed(str(e))

# --- NODE 2: EXECUTE STEPS VIA AI & PLAYWRIGHT ---
class PlaywrightAgentNode(BaseNode):
    async def execute(self, context: WorkflowContext, session=None):
        if context.failed: return

        # 1. Get Tools
        print("   🔌 Fetching Playwright Tools...")
        tools = await session.list_tools()
        
        tools_schema = []
        for t in tools.tools:
            # Safely get the schema property
            schema = getattr(t, 'inputSchema', getattr(t, 'input_schema', {}))
            tools_schema.append({
                "name": t.name,
                "description": t.description,
                "inputSchema": schema 
            })

        # 2. Initialize Chat History
        messages = [{
            "role": "user", 
            "parts": ["You are a QA Automation Agent. Execute the test steps precisely using the provided tools."]
        }]

        total_steps = len(context.steps_queue)
        
        for i, step in enumerate(context.steps_queue):
            if context.failed: break
            
            print(f"\n▶️  Step {i+1}/{total_steps}: {step}")
            messages.append({"role": "user", "parts": [f"Execute this step: {step}"]})

            try:
                response = get_ai_response(messages, tools_schema)

                # --- HANDLE TOOL CALL ---
                # Check the first part of the response for a function call
                part = response.parts[0]
                
                if fn := part.function_call:
                    tool_name = fn.name
                    tool_args = dict(fn.args)
                    
                    print(f"   🛠️  AI Action: {tool_name} {tool_args}")
                    
                    # Execute on Playwright Server
                    result = await session.call_tool(tool_name, arguments=tool_args)
                    
                    print(f"   ✅ Tool Result: {str(result)[:100]}...")
                    
                    # Update History (Important: Pass function response back)
                    # Note: Gemini expects function responses in a specific format, 
                    # but for simplicity in this loop we just append the result as context.
                    messages.append({"role": "model", "parts": [part]})
                    messages.append({
                        "role": "function", 
                        "name": tool_name, 
                        "parts": [{"function_response": {"name": tool_name, "response": {"result": str(result)}}}]
                    })

                else:
                    print(f"   ℹ️  AI Note: {part.text}")
                    messages.append({"role": "model", "parts": [part.text]})

                await asyncio.sleep(2)

            except Exception as e:
                print(f"   ❌ Execution Failed: {e}")
                context.mark_failed(str(e))
                break