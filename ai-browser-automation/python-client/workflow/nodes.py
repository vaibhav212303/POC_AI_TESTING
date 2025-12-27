import os
import json
import asyncio
from abc import ABC, abstractmethod
from workflow.state import WorkflowContext
from utils.file_parser import read_test_steps
from core.ai import get_ai_response
from utils.generators import generate_pom_code, generate_spec_code
from utils.optimizer import optimize_code

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.getcwd()))
SERVER_DIR = os.path.abspath(os.path.join(os.getcwd(), "../playwright-server"))
PAGES_DIR = os.path.join(SERVER_DIR, "tests", "pages")
SPECS_DIR = os.path.join(SERVER_DIR, "tests", "specs")

class BaseNode(ABC):
    @abstractmethod
    async def execute(self, context: WorkflowContext, session=None):
        pass

# --- NODE 1: LOAD STEPS FROM MARKDOWN (Kept as is) ---
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
            # Set test name from filename
            safe_name = os.path.basename(self.file_path).replace(".md", "").replace(" ", "_")
            context.test_name = safe_name
            print(f"   ✅ Loaded {len(steps)} steps.")
        except Exception as e:
            context.mark_failed(str(e))

# --- NODE 2: EXECUTE STEPS VIA AI & PLAYWRIGHT (With Recorder) --- 
class PlaywrightAgentNode(BaseNode):
    async def execute(self, context: WorkflowContext, session=None):
        if context.failed: return
        # 1. Get Tools
        print("   🔌 Fetching Playwright Tools...")
        tools = await session.list_tools()
        tools_schema = []
        for t in tools.tools:
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
                # Handle Gemini Response Structure
                # Note: get_ai_response returns the raw Gemini response object
                try:
                    part = response.candidates[0].content.parts[0]
                except:
                    # Fallback if structure varies
                    part = response.parts[0] if hasattr(response, 'parts') else None
                if part and part.function_call:
                    fn = part.function_call
                    tool_name = fn.name
                    tool_args = dict(fn.args)
                    print(f"   🛠️  AI Action: {tool_name} {tool_args}")
                    # Execute on Playwright Server
                    result = await session.call_tool(tool_name, arguments=tool_args)
                    print(f"   ✅ Tool Result: {str(result.content[0].text)[:100]}...")
                    # --- RECORDING LOGIC (Added to enable Node 3) ---
                    if tool_name in ["navigate", "click", "fill", "selectOption", "press"]:
                        context.recorded_history.append({
                            "action": tool_name,
                            "params": tool_args,
                            "description": step
                        })
                    # ------------------------------------------------
                    # Construct Function Response for Gemini History
                    messages.append({
                        "role": "model",
                        "parts": [part]
                    })
                    messages.append({
                        "role": "function",
                        "parts": [{
                            "function_response": {
                                "name": tool_name,
                                "response": {"result": str(result.content[0].text)}
                            }
                        }]
                    })
                else:
                    text = part.text if part else "No response"
                    print(f"   ℹ️  AI Note: {text}")
                    messages.append({"role": "model", "parts": [text]})
                await asyncio.sleep(1) # Small pause for stability
            except Exception as e:
                print(f"   ❌ Execution Failed: {e}")
                context.mark_failed(str(e))
                break

# --- NODE 3: VERIFIED POM GENERATOR ---
class VerifiedPomNode(BaseNode):
    async def execute(self, context: WorkflowContext, session=None):
        if context.failed: return
        print(f"\n--- 🏗️ NODE 3: POM Generation ---")
        if not context.recorded_history:
            print("   ⚠️ No actions recorded. Skipping POM generation.")
            return
        # Prepare data for generator
        history_json = json.dumps({"title": context.test_name, "steps": context.recorded_history})
        # Generate Code
        pom_name, pom_code = generate_pom_code(history_json)
        # Save File
        if not os.path.exists(PAGES_DIR): os.makedirs(PAGES_DIR)
        pom_path = os.path.join(PAGES_DIR, f"{pom_name}Page.ts")
        with open(pom_path, "w") as f:
            f.write(pom_code)
        print(f"   📄 Generated: {pom_name}Page.ts")
        # Optimize
        optimize_code(pom_path, file_type="POM")
        # Update Context for next node
        context.pom_class_name = pom_name
        context.pom_path = pom_path

# --- NODE 4: SPEC GENERATOR ---
class VerifiedSpecNode(BaseNode):
    async def execute(self, context: WorkflowContext, session=None):
        if context.failed or not context.pom_class_name: return
        print(f"\n--- 🧪 NODE 4: Spec Generation ---")
        history_json = json.dumps({"title": context.test_name, "steps": context.recorded_history})
        # Generate Spec
        spec_code = generate_spec_code(history_json, context.pom_class_name)
        # Save File
        if not os.path.exists(SPECS_DIR): os.makedirs(SPECS_DIR)
        spec_path = os.path.join(SPECS_DIR, f"{context.test_name}.spec.ts")
        with open(spec_path, "w") as f:
            f.write(spec_code)
        print(f"   📄 Generated: {context.test_name}.spec.ts")
        # Optimize
        optimize_code(spec_path, file_type="Spec")
        context.spec_path = spec_path