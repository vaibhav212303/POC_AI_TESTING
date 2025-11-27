import os
from ai_handler import get_ai_response, active_model

def heal_code(pom_path, error_log):
    print(f"❤️‍🩹 Attempting to heal: {pom_path}")
    
    with open(pom_path, "r") as f:
        current_code = f.read()

    prompt = f"""
    You are a Self-Healing AI. A Playwright test failed.
    
    ERROR LOG:
    {error_log}
    
    CURRENT POM CODE:
    {current_code}
    
    TASK:
    1. Identify the selector causing the error.
    2. Rewrite the code with a more robust selector (e.g., use text, layout, or accessibility role).
    3. Return the FULL FIXED CODE only.
    """
    
    resp = get_ai_response([{"role": "user", "content": prompt}], [])
    text = resp.text if active_model == "gemini" else resp.content[0].text if active_model == "claude" else resp.content
    fixed_code = text.replace("```typescript", "").replace("```", "").strip()
    
    with open(pom_path, "w") as f:
        f.write(fixed_code)
    
    print("✅ Code patched.")