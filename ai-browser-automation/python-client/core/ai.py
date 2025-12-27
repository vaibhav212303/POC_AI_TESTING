import os
import time
from dotenv import load_dotenv
import google.generativeai as genai
from google.generativeai.types import FunctionDeclaration, Tool

load_dotenv()

# --- DYNAMIC CONFIGURATION STATE ---
# Default to what's in .env, or fallback to Gemini Flash
_CURRENT_CONFIG = {
    "provider": "gemini",
    "model_name": os.getenv("GEMINI_MODEL_NAME", "models/gemini-1.5-flash")
}

def set_active_model(provider, model_name=None):
    global _CURRENT_CONFIG
    _CURRENT_CONFIG["provider"] = provider
    # Set default model names if none provided
    if not model_name:
        if provider == "gemini":
            model_name = "models/gemini-1.5-flash"
        elif provider == "openai":
            model_name = "gpt-4o"
    _CURRENT_CONFIG["model_name"] = model_name
    print(f"\n🔄 Switched AI to: {provider.upper()} ({model_name})")

def clean_schema(schema):
    if isinstance(schema, dict):
        # Remove unsupported keys
        schema.pop("additionalProperties", None)
        schema.pop("title", None)
        # Recurse into common nested structures
        for key, value in schema.items():
            if isinstance(value, (dict, list)):
                clean_schema(value)
    elif isinstance(schema, list):
        for item in schema:
            clean_schema(item)
    return schema

def get_ai_response(messages, tools_schema=None):
    if tools_schema is None:
        tools_schema = []
    # Get current dynamic settings
    active_provider = _CURRENT_CONFIG["provider"]
    model_name = _CURRENT_CONFIG["model_name"]
    print(f"🧠 Thinking ({active_provider} : {model_name})...")
    # --- RETRY LOGIC WRAPPER ---
    max_retries = 5
    attempt = 0
    while attempt < max_retries:
        try:
            if active_provider == "gemini":
                genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
                # 1. Setup Tools
                tools = []
                if tools_schema:
                    gemini_funcs = []
                    for t in tools_schema:
                        # --- FIX: CLEAN THE SCHEMA ---
                        raw_schema = t.get("inputSchema", t.get("parameters", {}))
                        sanitized_schema = clean_schema(raw_schema.copy()) 
                        gemini_funcs.append(
                            FunctionDeclaration(
                                name=t["name"], 
                                description=t["description"], 
                                parameters=sanitized_schema
                            )
                        )
                    tools = [Tool(function_declarations=gemini_funcs)]
                # Use dynamic model name
                model = genai.GenerativeModel(model_name=model_name, tools=tools)
                # 2. Format History for Gemini
                gemini_history = []
                for msg in messages:
                    role = "user" if msg["role"] in ["user", "system"] else "model"
                    parts = []
                    # --- Support both 'parts' and 'content' keys ---
                    if "parts" in msg:
                        # Caller already provided Gemini format
                        parts = msg["parts"]
                    elif "content" in msg:
                        # Convert OpenAI format to Gemini
                        content = msg["content"]
                        if isinstance(content, str):
                            parts.append(content)
                        elif isinstance(content, list):
                            for item in content:
                                if item.get("type") == "text":
                                    parts.append(item["text"])
                    gemini_history.append({"role": role, "parts": parts})
                
                # Execute Chat
                if len(gemini_history) > 1:
                    chat_history = gemini_history[:-1]
                    last_message = gemini_history[-1]["parts"]
                    chat = model.start_chat(history=chat_history)
                    response = chat.send_message(last_message)
                else:
                    chat = model.start_chat(history=[])
                    response = chat.send_message(gemini_history[0]["parts"])
                return response

        except Exception as e:
            error_str = str(e)
            # Detect Rate Limit / Quota errors (429)
            if "429" in error_str or "quota" in error_str.lower() or "ResourceExhausted" in error_str:
                attempt += 1
                wait_time = 10 * attempt # Wait 10s, 20s, 30s...
                print(f"\n⏳ Rate Limit Hit. Waiting {wait_time}s before retry ({attempt}/{max_retries})...")
                time.sleep(wait_time)
            elif "404" in error_str:
                print(f"\n❌ Model '{model_name}' not found. Check .env or set_active_model.")
                raise e
            else:
                print(f"❌ Gemini API Error: {e}")
                raise e
    return None