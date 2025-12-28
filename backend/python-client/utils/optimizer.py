import os
import re
from core.ai import get_ai_response, set_active_model
from utils.validator import PlaywrightValidator

# Setup Path to Server
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SERVER_DIR = os.path.join(BASE_DIR, "ai-browser-automation", "playwright-server")
# Adjust 'ai-browser-automation' if your root folder name differs

validator = PlaywrightValidator(SERVER_DIR)

def optimize_code(file_path, file_type="POM"):
    """
    Reads a file, sends it to the AI for a 'Senior QA Code Review',
    validates the output, and overwrites the file if improved.
    
    file_type: "POM" or "Spec"
    """
    if not os.path.exists(file_path):
        print(f"❌ Error: File not found at {file_path}")
        return

    filename = os.path.basename(file_path)
    print(f"\n✨ QA Optimizer is analyzing: {filename}...")
    
    with open(file_path, "r") as f:
        original_code = f.read()

    # 1. Switch to Smart Model (Pro) for Refactoring
    # Optimization requires reasoning, not just speed.
    # Ensure you have 'models/gemini-1.5-pro' in your list_models() capabilities
    set_active_model("gemini", "models/gemini-1.5-pro")

    # 2. Define the Persona and Rules based on file type
    if file_type == "POM":
        system_prompt = f"""
        You are a Senior Playwright Architect. Refactor the following Page Object Model (TypeScript).
        
        Class Name: {filename.replace('.ts', '')}
        
        OPTIMIZATION GOALS:
        1. SEMANTIC LOCATORS: Replace brittle CSS (e.g. 'div > .btn') with 'getByRole', 'getByPlaceholder', 'getByText' where possible.
        2. STRICT TYPING: Ensure 'readonly locator: Locator' is used for all elements.
        3. CLEAN CONSTRUCTOR: Initialize locators inside the constructor.
        4. READABILITY: Use descriptive method names (e.g. 'performLogin' instead of 'doIt').
        5. CLEANUP: Remove unused imports, console.logs, and commented code.
        
        RETURN ONLY THE OPTIMIZED TYPESCRIPT CODE. NO MARKDOWN.
        """
    else: # Spec
        system_prompt = """
        You are a Senior SDET. Refactor the following Playwright Test Spec (TypeScript).
        
        OPTIMIZATION GOALS:
        1. NO HARD WAITS: Delete any 'waitForTimeout', 'sleep', or 'setTimeout'. Use 'await expect().toBeVisible()' instead.
        2. ISOLATION: Ensure tests are independent.
        3. BEST PRACTICES: Use 'test.step' blocks if the test is long.
        4. ASSERTIONS: Ensure 'await expect(page).toHaveScreenshot()' is present if a visual check is implied.
        5. CLEANUP: Remove redundant comments.
        
        RETURN ONLY THE OPTIMIZED TYPESCRIPT CODE. NO MARKDOWN.
        """

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"CURRENT CODE:\n{original_code}"}
    ]

    # 3. Get Optimized Code
    try:
        resp = get_ai_response(messages)
        
        # Handle different response structures safely
        if hasattr(resp, 'text'):
            optimized_code = resp.text
        elif hasattr(resp, 'content'):
            if isinstance(resp.content, list):
                optimized_code = resp.content[0].text
            else:
                optimized_code = str(resp.content)
        else:
            # Fallback
            optimized_code = str(resp)

    except Exception as e:
        print(f"   ❌ AI Error during optimization: {e}")
        set_active_model("gemini", "models/gemini-1.5-flash") # Reset
        return

    # Clean Markdown formatting
    optimized_code = optimized_code.replace("```typescript", "").replace("```", "").strip()

    # 4. Safety Check: Validate the new code
    # We strictly validate the optimized code before overwriting the user's file.
    is_valid = False
    err_msg = ""

    if file_type == "POM":
        class_name = filename.replace(".ts", "")
        is_valid, err_msg = validator.validate_pom(optimized_code, class_name)
    else:
        # For specs, extract the POM class name from imports to validate
        match = re.search(r'import\s+(\w+)Page\s+from', original_code)
        pom_class = match.group(1) if match else "Unknown"
        is_valid, err_msg = validator.validate_spec(optimized_code, pom_class)

    # 5. Apply Changes
    if is_valid:
        with open(file_path, "w") as f:
            f.write(optimized_code)
        print(f"   ✅ Optimization successfully applied.")
    else:
        print(f"   ⚠️ Optimization discarded. AI produced invalid code.")
        print(f"      Reason: {err_msg}")

    # 6. Reset Model
    set_active_model("gemini", "models/gemini-1.5-flash")