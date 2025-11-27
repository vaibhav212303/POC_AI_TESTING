import os
import json
from ai_handler import get_ai_response, active_model
from validator import PlaywrightValidator 

BASE_DIR = os.path.dirname(os.getcwd())
SERVER_DIR = os.path.join(BASE_DIR, "playwright-server")

# Initialize Validator
validator = PlaywrightValidator(SERVER_DIR)

def fix_code_with_ai(bad_code, error_messages, context):
    """
    The 'Fixer' Agent. It only runs if the Validator found concrete errors.
    """
    print(f"   🔧 Validator found errors in {context}. AI Fixing...")
    print(f"      Errors: {error_messages}")

    prompt = f"""
    You are a Playwright Code Fixer. The previous code you wrote has specific errors.
    
    CONTEXT: {context}
    
    FAILED CODE:
    {bad_code}
    
    SPECIFIC ERRORS TO FIX:
    {error_messages}
    
    RULES:
    1. Fix ONLY the reported errors.
    2. Maintain the rest of the logic.
    3. Return ONLY valid TypeScript code.
    """
    
    resp = get_ai_response([{"role": "user", "content": prompt}], [])
    text = resp.text if active_model == "gemini" else resp.content[0].text if active_model == "claude" else resp.content
    return text.replace("```typescript", "").replace("```", "").strip()

# --- GENERATORS ---

def generate_manual_test_proposal(url, page_content):
    # (Same as before, no changes needed here)
    prompt = f"""
    Analyze this page content and URL ({url}).
    Generate 1 critical 'Happy Path' manual test case in JSON format.
    Format: {{ "id": "...", "title": "...", "steps": [...], "verification": "..." }}
    Page Content Snippet: {page_content[:2000]}
    RETURN ONLY JSON.
    """
    resp = get_ai_response([{"role": "user", "content": prompt}], [])
    text = resp.text if active_model == "gemini" else resp.content[0].text if active_model == "claude" else resp.content
    return text.replace("```json", "").replace("```", "").strip()

def generate_pom_code(manual_test_json):
    data = json.loads(manual_test_json)
    name = data['title'].replace(" ", "")
    
    # 1. Generate Draft
    prompt = f"""
    Create a Playwright Page Object Model (TypeScript).
    Class Name: {name}Page
    File Name: {name}Page.ts
    Input Data: {json.dumps(data)}
    Rules:
    1. Import: import {{ type Page }} from "playwright/test";
    2. Constructor: constructor(readonly page: Page) {{ }}
    3. Methods: async stepName() {{ }}
    4. Export default class.
    5. RETURN ONLY CODE.
    """
    resp = get_ai_response([{"role": "user", "content": prompt}], [])
    code = resp.text if active_model == "gemini" else resp.content[0].text if active_model == "claude" else resp.content
    code = code.replace("```typescript", "").replace("```", "").strip()

    # 2. VALIDATION LOOP
    is_valid, error_msg = validator.validate_pom(code, name)
    if not is_valid:
        # Loop once to fix (prevent infinite loops, usually 1 pass is enough)
        code = fix_code_with_ai(code, error_msg, "Page Object Model")
    
    return name, code

def generate_spec_code(manual_test_json, pom_class_name):
    data = json.loads(manual_test_json)
    
    # 1. Generate Draft
    prompt = f"""
    Create a Playwright Test Spec.
    Imports:
    1. import {{ test, expect }} from "playwright/test";
    2. import {pom_class_name}Page from '../pages/{pom_class_name}Page';
    
    Test Data: {json.dumps(data)}
    Rules:
    1. Structure: test('{data['title']}', async ({{ page }}) => {{ ... }});
    2. Instantiate: const p = new {pom_class_name}Page(page);
    3. Call methods.
    4. RETURN ONLY CODE.
    """
    resp = get_ai_response([{"role": "user", "content": prompt}], [])
    code = resp.text if active_model == "gemini" else resp.content[0].text if active_model == "claude" else resp.content
    code = code.replace("```typescript", "").replace("```", "").strip()

    # 2. VALIDATION LOOP
    is_valid, error_msg = validator.validate_spec(code, pom_class_name)
    if not is_valid:
        code = fix_code_with_ai(code, error_msg, "Test Spec File")
        
    return code