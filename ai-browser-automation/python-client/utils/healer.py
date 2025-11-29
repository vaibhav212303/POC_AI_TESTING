from core.ai import get_ai_response, ACTIVE_MODEL

def heal_code(pom_path, error_log):
    print(f"❤️‍🩹 Healing POM: {pom_path}")
    with open(pom_path, "r") as f: code = f.read()

    prompt = f"""
    Fix Playwright Selector Errors.
    ERROR: {error_log}
    CODE: {code}
    Task: Update selectors to be more robust (text/accessibility).
    RETURN ONLY FULL FIXED CODE.
    """
    
    resp = get_ai_response([{"role": "user", "content": prompt}])
    fixed_code = resp.text if ACTIVE_MODEL == "gemini" else resp.content
    fixed_code = fixed_code.replace("```typescript", "").replace("```", "").strip()
    
    with open(pom_path, "w") as f: f.write(fixed_code)
    print("✅ POM Patched.")