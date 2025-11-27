import os
from ai_handler import get_ai_response, active_model

# Define the target directory relative to this script
BASE_DIR = os.path.dirname(os.getcwd())
TEST_DIR = os.path.join(BASE_DIR, "playwright-server", "tests")

def ensure_test_dir():
    if not os.path.exists(TEST_DIR):
        os.makedirs(TEST_DIR)
    return TEST_DIR

def get_existing_tests():
    """Returns a list of .spec.ts files in the tests folder."""
    ensure_test_dir()
    return [f for f in os.listdir(TEST_DIR) if f.endswith(".spec.ts")]

def generate_test_file(action_history, filename=None, mode="new"):
    """
    mode: 'new' = Create fresh file.
    mode: 'update' = Read existing file and append/merge new actions.
    """
    print(f"\n📝 Generating test code ({mode} mode)...")
    ensure_test_dir()

    # 1. Prepare Action History Text
    actions_text = ""
    for i, action in enumerate(action_history):
        actions_text += f"{i+1}. Tool: {action['tool']}\n   Args: {action['args']}\n   Result: {action['result']}\n\n"

    # 2. handle UPDATE vs NEW
    existing_code = ""
    if mode == "update" and filename:
        file_path = os.path.join(TEST_DIR, filename)
        if os.path.exists(file_path):
            with open(file_path, "r") as f:
                existing_code = f.read()
            print(f"📖 Read existing file: {filename}")
        else:
            print(f"⚠️ File {filename} not found, switching to NEW mode.")
            mode = "new"

    # 3. Construct Prompt
    if mode == "new":
        system_prompt = """
        You are an expert Playwright/TypeScript Engineer.
        Convert the RECORDED ACTIONS into a new runnable test file.
        Rules:
        1. Import { test, expect } from "playwright/test".
        2. Create a test block test('AI Generated Flow', ...).
        3. Return ONLY code.
        """
        user_content = f"Actions:\n{actions_text}"
    else:
        # UPDATE MODE PROMPT
        system_prompt = """
        You are an expert Playwright Engineer.
        Your task is to UPDATE an existing test file with NEW actions.
        
        Rules:
        1. Analyze the EXISTING CODE.
        2. Analyze the NEW ACTIONS.
        3. Append a NEW test('...', ...) block at the end of the file for the new actions.
        4. Keep the existing imports and existing tests exactly as they are.
        5. Return the FULL updated file content.
        6. Return ONLY code.
        """
        user_content = f"EXISTING CODE:\n{existing_code}\n\nNEW ACTIONS:\n{actions_text}"

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_content}
    ]

    # 4. Call AI
    response = get_ai_response(messages, [])
    
    # 5. Extract Code
    code = ""
    if active_model == "gemini":
        code = response.text 
    elif active_model == "openai":
        code = response.content
    elif active_model == "claude":
        code = response.content[0].text

    code = code.replace("```typescript", "").replace("```", "").strip()

    # 6. Save
    # If filename wasn't provided, ask for one (or default)
    if not filename:
        filename = "generated_test.spec.ts"
    
    output_path = os.path.join(TEST_DIR, filename)
    with open(output_path, "w") as f:
        f.write(code)
    
    print(f"🚀 Test Code saved to: {output_path}")
    return code