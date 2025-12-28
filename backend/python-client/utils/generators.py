import json
import os
from core.ai import get_ai_response  # Removed ACTIVE_MODEL import
from utils.validator import PlaywrightValidator

# Setup paths relative to this file
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SERVER_DIR = os.path.join(BASE_DIR, "ai-browser-automation", "playwright-server") 

validator = PlaywrightValidator(SERVER_DIR)

# --- HELPER: Handle different AI response formats dynamically ---
def extract_ai_text(resp):
    """
    Automatically detects if response is from Gemini (has .text) 
    or OpenAI/Claude (has .content).
    """
    try:
        # Gemini
        if hasattr(resp, 'text'):
            return resp.text
        
        # OpenAI / Claude
        if hasattr(resp, 'content'):
            # Claude returns a list of content blocks
            if isinstance(resp.content, list):
                return resp.content[0].text
            # OpenAI returns a string
            return resp.content
            
    except Exception as e:
        print(f"⚠️ Error extracting text: {e}")
        
    return str(resp)

# ---------------------------------------------------------------

def fix_code_with_ai(bad_code, error_messages, context):
    print(f"   🔧 Fixing {context} errors...")
    prompt = f"""
    Fix this Playwright code based on errors.
    CONTEXT: {context}
    ERRORS: {error_messages}
    CODE: {bad_code}
    RETURN ONLY FIXED TYPESCRIPT CODE.
    """
    resp = get_ai_response([{"role": "user", "content": prompt}])
    
    # Use helper instead of checking model name
    text = extract_ai_text(resp)
    
    return text.replace("```typescript", "").replace("```", "").strip()

def generate_pom_code(manual_test_json):
    data = json.loads(manual_test_json)
    name = data['title'].replace(" ", "")
    
    prompt = f"""
    Create Playwright POM (TypeScript).
    Class: {name}Page
    Data: {json.dumps(data)}
    Rules:
    1. Import {{ type Page }} from "playwright/test";
    2. Export default class {name}Page.
    3. Define selectors as readonly.
    4. Async methods for steps.
    RETURN ONLY CODE.
    """
    
    resp = get_ai_response([{"role": "user", "content": prompt}])
    
    # Use helper
    code = extract_ai_text(resp)
    code = code.replace("```typescript", "").replace("```", "").strip()

    # Validation
    is_valid, msg = validator.validate_pom(code, name)
    if not is_valid:
        code = fix_code_with_ai(code, msg, "POM")
    
    return name, code

def generate_spec_code(manual_test_json, pom_class_name):
    data = json.loads(manual_test_json)
    
    prompt = f"""
    Create Playwright Spec.
    Data: {json.dumps(data)}
    Rules:
    1. import {{ test, expect }} from "playwright/test";
    2. import {pom_class_name}Page from '../pages/{pom_class_name}Page';
    3. test('{data['title']}', async ({{ page }}) => {{ ... }});
    4. Add visual assertion: await expect(page).toHaveScreenshot();
    RETURN ONLY CODE.
    """
    
    resp = get_ai_response([{"role": "user", "content": prompt}])
    
    # Use helper
    code = extract_ai_text(resp)
    code = code.replace("```typescript", "").replace("```", "").strip()

    # Validation
    is_valid, msg = validator.validate_spec(code, pom_class_name)
    if not is_valid:
        code = fix_code_with_ai(code, msg, "Spec")
    
    return code

def generate_manual_test_proposal(url, page_content):
    prompt = f"""
    Analyze page ({url}). Generate 1 Happy Path test JSON.
    Format: {{ "id": "..", "title": "..", "steps": [..], "verification": ".." }}
    Content: {page_content[:1500]}
    RETURN ONLY JSON.
    """
    resp = get_ai_response([{"role": "user", "content": prompt}])
    
    # Use helper
    text = extract_ai_text(resp)
    
    return text.replace("```json", "").replace("```", "").strip()